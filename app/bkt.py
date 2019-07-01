import pandas as pd
import numpy as np

# params
INIT = 'init'
TRANSFER = 'trasfer'
SLIP = 'slip'
GUESS = 'guess'

# terms
CONCEPT = 'concept'
CONCEPTS_STR = 'concepts'
ADJ_MAT_STR = "adjMat"
EID = "eid"
UID = 'uid'
STEP = 'step'
CORRECT = 'correct'
IS_READ = 'is_read'


def posterior_pknown(is_correct, eid, transfer, item_params, prior_pknown):
    """
    updates BKT estimate of learner knowledge

    Parameters
    ----------
    result: boolean
        True if response was correct
    eid: String
        exercise ID
    transfer: float
        transfer probability for concept
    item_params: pd.DataFrame
        slip and guess parameters for each item
    prior_pknown: float
        prior probability user learned this concept (read, write are different concepts)
    """
    if not eid in item_params[EID].unique():
        raise Exception(
            'Given exercise ID not in response data. Return w/ no update. EID is {}'.format(eid))
        return prior_pknown

    posterior = -1.0

    # .iloc[0] added to get 1st one (just in case exercise ID duplicated to handle error condition where exercise is read & write)
    slip = float(item_params[item_params[EID] == eid][SLIP].iloc[0]) 
    guess = float(item_params[item_params[EID] == eid][GUESS].iloc[0])

    if is_correct:
        posterior = (prior_pknown * (1.0 - slip)) / ((prior_pknown * (1 - slip)) + ((1.0-prior_pknown)*guess))
    else:
        posterior = (prior_pknown * slip) / ((prior_pknown * slip) + ((1.0-prior_pknown)*(1.0-guess)))
    
    return (posterior + (1.0-posterior) * transfer)


def pknown_seq(uid, concept, df_opp, concept_params, item_params, is_read=True):
    """
    Predict sequence of probability a concept is known after each step.
    Function not used in real-time, but may be used to batch update pknown (e.g. if concept or exercise params updated)
    
    Parameters
    ----------
    uid: String
        learner/user ID
    concept: String
        concept name
    df_opp: pd.DataFrame
        dataframe which records the correctness of responses for users. columns: uid, eid, step, correct
    concept_params: pd.DataFrame
        concept parameters (concept, init, transfer)
    item_params: pd.DataFrame
        item parameters (eid, slip, guess, concept)
    is_read: Boolean
        True if concept relates to reading, False if it relates to writing
    """
    
    eids = item_params[(item_params[CONCEPT] == concept) & (item_params[IS_READ] == is_read)][EID]
    
    # grab exercise sequence for specific user working on specific concept
    exercise_seq = df_opp[(df_opp[UID] == uid) & (df_opp[EID].isin(eids))]
    
    n_opps = len(exercise_seq) # number exercises attempted
    
    # filtering for 1 concept to update
    concept_params_target = concept_params[(concept_params[CONCEPT] == concept) & (concept_params[IS_READ] == is_read)]
    
    pk = pd.Series(np.zeros(n_opps + 1))    
    pk[0] = float(concept_params_target[INIT])
    
    if(n_opps > 0):
        transfer = float(concept_params_target[TRANSFER])        
        
        for step in range(1,n_opps+1):
            df_step = exercise_seq[exercise_seq[STEP]==step]
            if(len(df_step) != 1):
                raise Exception('Did not find exactly 1 response for user {} for step {}. Found {}'
                                .format(uid, step, len(df_step)))

            is_correct = df_step.iloc[0][CORRECT]
            eid = df_step.iloc[0][EID]
            
            pk[step] = posterior_pknown(is_correct, eid, transfer, item_params, pk[step - 1])
    return pk


def pcorrect(pk, slip, guess):
    return (pk * (1.0-slip)) + ((1.0 - pk) * guess)


def pcorrect_seq(uid, concept, df_opp, concept_params, item_params, is_read=True):
    """
    Probability of correct responses predicted by BKT.
    
    Parameters
    ----------
    uid: String
        learner/user ID
    concept: String
        concept name
    df_opp: pd.DataFrame
        dataframe which records the correctness of responses for users. columns: uid, eid, step, correct
    concept_params: pd.DataFrame
        concept parameters (concept, init, transfer)
    item_params: pd.DataFrame
        item parameters (eid, slip, guess, concept)
    is_read: Boolean
        True if concept relates to reading, False if it relates to writing    
    """
    eids = item_params[item_params[CONCEPT] == concept][EID]
    
    # grab exercise sequence for specific user working on specific concept
    exercise_seq = df_opp[(df_opp[UID] == uid) & (df_opp[EID].isin(eids))]    
    n_opps = len(exercise_seq) # number exercises attempted

    pk = pknown_seq(uid, concept, df_opp, concept_params, item_params, is_read)
    pc = pd.Series(np.zeros(n_opps))
    for step in range(0,len(pc)):
        eid = exercise_seq.iloc[step][EID]
        slip = float(item_params[item_params[EID] == eid][SLIP])
        guess = float(item_params[item_params[EID] == eid][GUESS])
        pc[step] = pcorrect(pk[step], slip, guess)

    return pc


def order_next_questions(exercise_ids, pk, item_params, error = 0.0, penalty = 1.0):
    """
    Order questions based on "most answerable." 
    Exercise IDs and probability of known must be of same concept, either read or write.
    
    Parameters
    ----------
    exercise_ids: list
        list of exercise ids (Strings) for same concept
    pk: float
        probability concept is known
    item_params: pd.DataFrame
        item parameters (eid, slip, guess, concept)
    """
    df_output = pd.DataFrame({"eid": exercise_ids, "score": np.zeros(len(exercise_ids))})
    df_item_params = pd.DataFrame.from_dict(item_params)
    
    # get max and min scores/p(correct)
    for eid in exercise_ids:
        if eid in list(df_item_params):
            params = df_item_params[df_item_params[EID] == eid].iloc[0]
            df_output.loc[df_output[EID] == eid, 'score'] = pcorrect(pk, params[SLIP], params[GUESS])

    min_score = min(df_output['score'])
    max_score = max(df_output['score'])
    target_score = min_score + ((max_score - min_score) * (1 - pk + error))
    
    df_output['diff'] = abs(df_output['score'] - target_score) * penalty
    
    return list(df_output.sort_values(by='diff')[EID])

def filter_ordered_questions_by_concepts(questions, item_params, target_concept, concept_map, 
                                         max_num_target=4, max_num_child=2, max_num_parent=2):
    """
    Given ordered concept, filter recommendations such that there are at most the max number 
    for a target concept and parent & child concepts. 
    Recommendations returned in order from most to least recommended.
    
    Parameters
    ----------
    questions: list
        ordered list of exercise ids (strings) where index 0 is 1st (most recommended) exercise
    item_params: pd.DataFrame
        item parameters (eid, slip, guess, concept)
    target_concept: string
        
    concept_map: dict
        dictionary with 2 attributes: {concepts, adjMat}. 
        adjMat is a list of lists which serves as an adjacency matrix for the concept map (directed graph)
        concepts is a list of concepts where a concept at index i maps to the same index on adjMat
    max_num_target: int
        maximum number of recommendations for a target concept. Must be >=0
    max_num_child: int
        maximum number of recommendations for a child of the target concept. Must be >= 0
    max_num_parent: int
        maximum number of recommendations for a parent of the target concept. Must be >=0
    """ 
    
    def get_parents(target, concept_map):
        """
        Given a target concept, return a list of concept IDs for parent concepts
        """
        parents = []
        target_index = concept_map[CONCEPTS_STR].index(target)
        for row in range(len(concept_map[ADJ_MAT_STR])): 
            # get value in adjMat for each row at target concept's col
            val = concept_map[ADJ_MAT_STR][row][target_index] 
            if val > 0 and target_index != row: # don't care concepts are their own parents
                print('parent found at {}, {}'.format(row, target_index)) # TODO remove
                parents.append(concept_map[CONCEPTS_STR][row])
        return parents

    def get_children(target, concept_map):
        """
        Given a target concept, return a list of concept IDs for all child concepts
        """
        child_inds = []
        target_index = concept_map[CONCEPTS_STR].index(target)
        target_row = concept_map[ADJ_MAT_STR][target_index]
        for ind in range(len(target_row)): # for each ind in row of adj mat
            val = target_row[ind]
            if(val>0 and ind != target_index): # don't care concept is child of itself
                child_inds.append(ind)
        return list(map(lambda ind: concept_map[CONCEPTS_STR][ind], child_inds))

    def get_concept(eid, item_params):
        """
        Given a question/exercise eid (String) and item_params (pd.DataFrame),
        return the concept that exercise corresponds to.

        Assumes eid is unique (maps to exactly 1 row)
        """

        concept = item_params[item_params[EID]==eid][CONCEPT]

        if len(concept) < 1: # TODO: make this filter "!= 1" to be more strict
            raise Exception("Exercise ID does not map to any exercises. eid: {}".format(eid))
        else:
            return concept.iloc[0] # to get actual value
    
    df_item_params = pd.DataFrame.from_dict(item_params)

    rec_eids = []

    # add max_num_target questions of same concept to rec_eids
    rec_target = list(filter(lambda q: get_concept(q, df_item_params) == target_concept, 
                          questions))[:max_num_target]
    print("For target, added {}".format(rec_target))
    rec_eids += rec_target
                

    # add max_num_child questions of child concepts to rec_eids
    rec_child = list(filter(lambda q: get_concept(q, df_item_params) in get_children(target_concept, concept_map), 
                          questions))[:max_num_child]
    print("For children, added {}".format(rec_child ))
    rec_eids += rec_child

    # add max_num_parent questions of parent concepts to rec_eids
    rec_parent = list(filter(lambda q: get_concept(q, df_item_params) in get_parents(target_concept, concept_map), 
                          questions))[:max_num_parent] 
    print("For parents, added {}".format(rec_parent))
    rec_eids += rec_parent                             

    # want order of recommendations to stay same & only grab from top half of recommendations
    return list(filter(lambda eid: eid in rec_eids, questions[:int(len(questions)/2)+1])) 