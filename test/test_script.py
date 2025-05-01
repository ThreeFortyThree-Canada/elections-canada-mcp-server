#!/usr/bin/env python3
"""
Test script to answer complex questions about the 2021 Canadian federal election data
using pandas and data analysis techniques.
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

# Path to the data file
DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "datafiles/2021_riding_vote_redistributed_ElectionsCanada.json"
)

# Path to questions file
QUESTIONS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "complex_questions.json"
)

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the election data and transform it into two DataFrames:
    1. riding_df: One row per riding with metadata
    2. votes_df: One row per party-riding combination with vote data
    """
    # Load the raw data
    with open(DATA_FILE, 'r') as f:
        election_data = json.load(f)
    
    # Create riding-level DataFrame
    riding_rows = []
    for riding in election_data:
        riding_rows.append({
            "ridingCode": riding["ridingCode"],
            "ridingName": riding["ridingName_EN"],
            "province": riding["provCode"],
            "validVotes": riding["validVotes"],
            "rejectedVotes": riding.get("rejectedVotes", 0),
            "totalVotes": riding["totalVotes"]
        })
    riding_df = pd.DataFrame(riding_rows)
    
    # Create votes DataFrame (one row per party-riding combination)
    vote_rows = []
    for riding in election_data:
        # Sort parties by votes to determine rankings
        sorted_parties = sorted(
            riding["voteDistribution"], 
            key=lambda x: x["votes"], 
            reverse=True
        )
        
        # Add ranking information
        for rank, party_data in enumerate(sorted_parties):
            vote_rows.append({
                "ridingCode": riding["ridingCode"],
                "ridingName": riding["ridingName_EN"],
                "province": riding["provCode"],
                "partyCode": party_data["partyCode"],
                "votes": party_data["votes"],
                "votePercent": party_data["votePercent"],
                "rank": rank + 1  # 1-based ranking (1st, 2nd, 3rd, etc.)
            })
    
    votes_df = pd.DataFrame(vote_rows)
    
    return riding_df, votes_df

def load_questions() -> List[Dict[str, str]]:
    """Load the complex questions from the JSON file"""
    with open(QUESTIONS_FILE, 'r') as f:
        return json.load(f)

def answer_question_1(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "How many ridings did the Liberals win in Ontario where the Conservative party 
    came in second with more than 30% of the vote?"
    """
    # Filter for Ontario ridings
    ontario_ridings = votes_df[votes_df['province'] == 'ON']
    
    # Find ridings where Liberals won (rank 1)
    liberal_wins = ontario_ridings[
        (ontario_ridings['partyCode'] == 'LPC') & 
        (ontario_ridings['rank'] == 1)
    ]['ridingCode'].unique()
    
    # Find ridings where Conservatives came second with >30% vote
    cpc_second = ontario_ridings[
        (ontario_ridings['partyCode'] == 'CPC') & 
        (ontario_ridings['rank'] == 2) & 
        (ontario_ridings['votePercent'] > 30)
    ]['ridingCode'].unique()
    
    # Find intersection of both conditions
    matching_ridings = set(liberal_wins).intersection(set(cpc_second))
    
    return f"The Liberals won {len(matching_ridings)} ridings in Ontario where the Conservative party came in second with more than 30% of the vote."

def answer_question_2(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "Which province had the closest margin of victory between the winning party 
    and the second-place party when averaged across all ridings?"
    """
    # Get first and second place for each riding
    first_place = votes_df[votes_df['rank'] == 1].copy()
    first_place.rename(columns={
        'partyCode': 'winner', 
        'votes': 'winner_votes', 
        'votePercent': 'winner_percent'
    }, inplace=True)
    
    second_place = votes_df[votes_df['rank'] == 2].copy()
    second_place.rename(columns={
        'partyCode': 'runner_up', 
        'votes': 'runner_up_votes', 
        'votePercent': 'runner_up_percent'
    }, inplace=True)
    
    # Merge to get both in same DataFrame
    merged = pd.merge(
        first_place[['ridingCode', 'province', 'winner', 'winner_percent']], 
        second_place[['ridingCode', 'runner_up', 'runner_up_percent']],
        on='ridingCode'
    )
    
    # Calculate margin
    merged['margin'] = merged['winner_percent'] - merged['runner_up_percent']
    
    # Group by province and calculate average margin
    province_margins = merged.groupby('province')['margin'].mean().reset_index()
    
    # Find province with smallest margin
    closest_province = province_margins.loc[province_margins['margin'].idxmin()]
    
    return f"The province with the closest average margin of victory was {closest_province['province']} with an average margin of {closest_province['margin']:.2f}% between the winning party and the runner-up across all ridings."

def answer_question_3(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "In ridings where the NDP finished third, what was their average vote percentage 
    in Quebec compared to British Columbia?"
    """
    # Filter for NDP in third place
    ndp_third = votes_df[
        (votes_df['partyCode'] == 'NDP') & 
        (votes_df['rank'] == 3)
    ]
    
    # Calculate average in Quebec
    qc_avg = ndp_third[ndp_third['province'] == 'QC']['votePercent'].mean()
    
    # Calculate average in BC
    bc_avg = ndp_third[ndp_third['province'] == 'BC']['votePercent'].mean()
    
    # Count ridings for context
    qc_count = len(ndp_third[ndp_third['province'] == 'QC'])
    bc_count = len(ndp_third[ndp_third['province'] == 'BC'])
    
    return f"In ridings where the NDP finished third, their average vote percentage was {qc_avg:.2f}% in Quebec ({qc_count} ridings) compared to {bc_avg:.2f}% in British Columbia ({bc_count} ridings)."

def answer_question_4(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "Which riding had the highest voter turnout (total votes as a percentage of 
    eligible voters) and what party won that riding?"
    """
    # Note: The data doesn't have eligible voters, so we'll use total votes
    # as a proxy for turnout (this is not accurate in real analysis)
    
    # Find riding with highest total votes
    highest_turnout_riding = riding_df.loc[riding_df['totalVotes'].idxmax()]
    
    # Find winning party in that riding
    winning_party = votes_df[
        (votes_df['ridingCode'] == highest_turnout_riding['ridingCode']) & 
        (votes_df['rank'] == 1)
    ]['partyCode'].iloc[0]
    
    return f"The riding with the highest total votes was {highest_turnout_riding['ridingName']} with {highest_turnout_riding['totalVotes']} votes. The {winning_party} party won this riding."

def answer_question_5(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "How many seats did the Bloc Québécois win in Quebec ridings where they received 
    between 30-40% of the vote, and how does this compare to the number of seats the 
    Conservatives won in Alberta with the same vote percentage range?"
    """
    # BQ wins in Quebec with 30-40% vote
    bq_wins = votes_df[
        (votes_df['province'] == 'QC') &
        (votes_df['partyCode'] == 'BQ') &
        (votes_df['rank'] == 1) &
        (votes_df['votePercent'] >= 30) &
        (votes_df['votePercent'] <= 40)
    ]
    
    # CPC wins in Alberta with 30-40% vote
    cpc_wins = votes_df[
        (votes_df['province'] == 'AB') &
        (votes_df['partyCode'] == 'CPC') &
        (votes_df['rank'] == 1) &
        (votes_df['votePercent'] >= 30) &
        (votes_df['votePercent'] <= 40)
    ]
    
    return f"The Bloc Québécois won {len(bq_wins)} seats in Quebec ridings where they received between 30-40% of the vote, compared to {len(cpc_wins)} seats that the Conservatives won in Alberta with the same vote percentage range."

def answer_question_6(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "In ridings where the Green Party received more than 10% of the vote, 
    what was the average performance of the People's Party of Canada?"
    """
    # Find ridings where Green Party got >10%
    green_ridings = votes_df[
        (votes_df['partyCode'] == 'GPC') & 
        (votes_df['votePercent'] > 10)
    ]['ridingCode'].unique()
    
    # Find PPC performance in those ridings
    ppc_in_green_ridings = votes_df[
        (votes_df['partyCode'] == 'PPC') & 
        (votes_df['ridingCode'].isin(green_ridings))
    ]
    
    avg_ppc = ppc_in_green_ridings['votePercent'].mean()
    
    return f"In the {len(green_ridings)} ridings where the Green Party received more than 10% of the vote, the People's Party of Canada averaged {avg_ppc:.2f}% of the vote."

def answer_question_7(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "Which party had the most consistent vote percentage across all ridings in Canada, 
    as measured by the standard deviation of their vote percentages?"
    """
    # Calculate standard deviation of vote percentages for each party
    party_std = votes_df.groupby('partyCode')['votePercent'].agg(['mean', 'std']).reset_index()
    
    # Filter for major parties (to avoid parties that ran in very few ridings)
    major_parties = ['LPC', 'CPC', 'NDP', 'BQ', 'GPC', 'PPC']
    party_std = party_std[party_std['partyCode'].isin(major_parties)]
    
    # Find party with lowest standard deviation
    most_consistent = party_std.loc[party_std['std'].idxmin()]
    
    return f"The {most_consistent['partyCode']} had the most consistent vote percentage across Canada with a standard deviation of {most_consistent['std']:.2f}% around their mean of {most_consistent['mean']:.2f}%."

def answer_question_8(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "In urban ridings (those containing 'Toronto', 'Montreal', 'Vancouver', 'Calgary', 
    'Ottawa', 'Edmonton', 'Winnipeg', or 'Halifax' in their names), how did the Liberal vote 
    share compare to their performance in rural ridings?"
    """
    # Define urban cities
    urban_patterns = ['Toronto', 'Montreal', 'Vancouver', 'Calgary', 
                      'Ottawa', 'Edmonton', 'Winnipeg', 'Halifax']
    
    # Create urban flag
    votes_df['urban'] = votes_df['ridingName'].apply(
        lambda x: any(city in x for city in urban_patterns)
    )
    
    # Filter for Liberal party
    liberal_votes = votes_df[votes_df['partyCode'] == 'LPC']
    
    # Calculate average by urban/rural
    urban_avg = liberal_votes[liberal_votes['urban']]['votePercent'].mean()
    rural_avg = liberal_votes[~liberal_votes['urban']]['votePercent'].mean()
    
    # Count ridings in each category
    urban_count = liberal_votes[liberal_votes['urban']]['ridingCode'].nunique()
    rural_count = liberal_votes[~liberal_votes['urban']]['ridingCode'].nunique()
    
    return f"The Liberal party averaged {urban_avg:.2f}% of the vote in {urban_count} urban ridings, compared to {rural_avg:.2f}% in {rural_count} rural ridings, a difference of {urban_avg - rural_avg:.2f} percentage points."

def answer_question_9(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "What was the total number of votes received by independent candidates across Canada, 
    and in which riding did an independent candidate receive their highest vote percentage?"
    """
    # Filter for independent candidates
    independents = votes_df[votes_df['partyCode'] == 'Ind']
    
    # Calculate total votes
    total_ind_votes = independents['votes'].sum()
    
    # Find highest percentage
    highest_ind = independents.loc[independents['votePercent'].idxmax()]
    
    return f"Independent candidates received a total of {total_ind_votes:,} votes across Canada. The highest vote percentage for an independent candidate was {highest_ind['votePercent']:.2f}% in {highest_ind['ridingName']} ({highest_ind['province']})."

def answer_question_10(riding_df: pd.DataFrame, votes_df: pd.DataFrame) -> str:
    """
    Answer: "If we define a 'battleground riding' as one where the difference between the first 
    and second place parties was less than 5% of the vote, how many battleground ridings were 
    there in each province, and which party won the most battleground ridings nationally?"
    """
    # Get first and second place for each riding
    first_place = votes_df[votes_df['rank'] == 1].copy()
    first_place.rename(columns={
        'partyCode': 'winner', 
        'votePercent': 'winner_percent'
    }, inplace=True)
    
    second_place = votes_df[votes_df['rank'] == 2].copy()
    second_place.rename(columns={
        'votePercent': 'runner_up_percent'
    }, inplace=True)
    
    # Merge to get both in same DataFrame
    merged = pd.merge(
        first_place[['ridingCode', 'province', 'winner', 'winner_percent']], 
        second_place[['ridingCode', 'runner_up_percent']],
        on='ridingCode'
    )
    
    # Calculate margin and identify battlegrounds
    merged['margin'] = merged['winner_percent'] - merged['runner_up_percent']
    battlegrounds = merged[merged['margin'] < 5]
    
    # Count by province
    province_counts = battlegrounds.groupby('province').size().reset_index(name='count')
    
    # Count wins by party
    party_wins = battlegrounds.groupby('winner').size().reset_index(name='wins')
    top_party = party_wins.loc[party_wins['wins'].idxmax()]
    
    # Format province counts
    province_results = ", ".join([f"{row['province']}: {row['count']}" for _, row in province_counts.iterrows()])
    
    return f"There were {len(battlegrounds)} battleground ridings (margin < 5%) across Canada, distributed by province as follows: {province_results}. The {top_party['winner']} won the most battleground ridings with {top_party['wins']} wins."

def main():
    """Main function to load data and answer all questions"""
    print("Loading election data...")
    riding_df, votes_df = load_data()
    
    print("Loading questions...")
    questions = load_questions()
    
    # Map question indices to answer functions
    answer_functions = [
        answer_question_1,
        answer_question_2,
        answer_question_3,
        answer_question_4,
        answer_question_5,
        answer_question_6,
        answer_question_7,
        answer_question_8,
        answer_question_9,
        answer_question_10
    ]
    
    print("\n=== ANSWERS TO COMPLEX QUESTIONS ===\n")
    
    # Answer each question
    for i, question in enumerate(questions):
        print(f"Q{i+1}: {question['question']}")
        
        # Call the appropriate answer function
        if i < len(answer_functions):
            try:
                answer = answer_functions[i](riding_df, votes_df)
                print(f"A{i+1}: {answer}\n")
            except Exception as e:
                print(f"Error answering question {i+1}: {str(e)}\n")
        else:
            print(f"No answer function defined for question {i+1}\n")

if __name__ == "__main__":
    main()
