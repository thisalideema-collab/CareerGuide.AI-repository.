
from src.recommender import recommend_programmes

sample_student = {
    "Student_Stage": "Completed A/L",
    "AL_Stream": "Physical Science",
    "Interests_Select_Up_to_3": "Information Technology, Data Science",
    "Education_Preference": "Degree"
}

results = recommend_programmes(sample_student, top_k=10)

print("CAREERGUIDE.AI RECOMMENDATION RESULTS")
print("Total recommendations:", len(results))

print(results[[
    "Programme_Name",
    "Institution_Name",
    "Matching_Score",
    "Academic_Eligibility",
    "Financial_Feasibility"
]].to_string(index=False))

print("\nXAI EXPLANATION:")
print(results.iloc[0]["XAI_Explanation"])

