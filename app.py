
#Import packages for the Streamlit dashboard
import streamlit as st
import pandas as pd
import networkx as nx
from node2vec import Node2Vec
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

#Load the dataset inside the dashboard
file_path = '/content/drive/MyDrive/Dataset.xlsx'
df = pd.read_excel(file_path, sheet_name = 'BINS_ONLY')

#Core firms in dataset
firms = ['GOOGLE', 'APPLE', 'META', 'AMAZON', 'MICROSOFT']

#AI capability categories
categories = ["APPLICATIONS", "MODELING", "DATA", "COMPUTE"]

#Size bins by deal
deal_bins = ["DEAL_SMALL", "DEAL_MEDIUM", "DEAL_LARGE"]

#Size bins by amount raised
amount_raised_bins = ["AMT_SMALL", "AMT_MEDIUM", "AMT_LARGE"]

#Size bins by number of employees
number_of_employees_bins = ["EMP_SMALL", "EMP_MEDIUM", "EMP_LARGE"]

#Standardize the columns for the knowledge graph
triples_df = pd.DataFrame(df, columns=["SUBJECT", "PREDICATE", "OBJECT"])
triples_df = triples_df.rename(columns={"SUBJECT": "head", "PREDICATE": "relation", "OBJECT": "tail"})
triples_df = triples_df.astype(str)

#Name bin nodes to ensure distinct embeddings across relation types
def name_bins(row):
    if row["relation"] == "DEAL_VALUE_CATEGORY":
        return f"DEAL_{row['tail']}"
    elif row["relation"] == "AMOUNT_RAISED_CATEGORY":
        return f"AMT_{row['tail']}"
    elif row["relation"] == "NUMBER_OF_EMPLOYEES_CATEGORY":
        return f"EMP_{row['tail']}"
    return row["tail"]

triples_df["tail"] = triples_df.apply(name_bins, axis=1)

#Initialize the graph and add it's edges in the dashboard
graph = nx.Graph()
for _, row in triples_df.iterrows():
    graph.add_edge(row["head"], row["tail"])

#Train the node2vec model in the dashboard
node2vec = Node2Vec(graph, dimensions=64, walk_length=30, num_walks=200)
model = node2vec.fit(window=10, min_count=1)

#Builds a graph based on a selected company and its acquisitions.
def build_graph(triples_df, selected_company, show_ai_category, show_deal_value, show_amount_raised, show_number_of_employees):
  graph_for_dashboard = nx.Graph()
  acquired_companies = set()

  #Identify acquired companies
  for x, row in triples_df.iterrows():
    if row["head"] == selected_company and row["relation"] == "ACQUIRES":
        acquired_companies.add(row["tail"])
        graph_for_dashboard.add_edge(row["head"], row["tail"], relation="ACQUIRES")

  #Add related information for acquired companies
  for y, row in triples_df.iterrows():
    h = row["head"]
    t = row["tail"]
    r = row["relation"]

    if r == "IS_A" and show_ai_category:
      if h in acquired_companies:
        graph_for_dashboard.add_edge(h, t, relation=r)

    if r == "DEAL_VALUE_CATEGORY" and show_deal_value:
      if h in acquired_companies:
        graph_for_dashboard.add_edge(h, t, relation=r)

    if r == "AMOUNT_RAISED_CATEGORY" and show_amount_raised:
      if h in acquired_companies:
        graph_for_dashboard.add_edge(h, t, relation=r)

    if r == "NUMBER_OF_EMPLOYEES_CATEGORY" and show_number_of_employees:
      if h in acquired_companies:
        graph_for_dashboard.add_edge(h, t, relation=r)

  return graph_for_dashboard

#Similarity matrices comparing GAFAM firms across different categorical variables
#Includes deal size, amount raised, number of employees, and AI capability category for acquired companies

#GAFAM firm similarity scores for AI capability categories (DATA, COMPUTE, MODELING, APPLICATIONS)
cat_matrix_display = []
for firm in firms:
  row = {"Firm": firm}
  for cat in categories:
    num = cosine_similarity([model.wv[firm]], [model.wv[cat]])[0][0]
    row[cat] = num
  cat_matrix_display.append(row)

cat_matrix_df = pd.DataFrame(cat_matrix_display)

#GAFAM firm similarity scores for deal value category bins
deal_bin_matrix = []

for firm in firms:
  row = {"Firm": firm}
  for b in deal_bins:
   num = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
   row[b] = num
  deal_bin_matrix.append(row)

deal_matrix_df = pd.DataFrame(deal_bin_matrix)

#GAFAM firm similarity scores for funding amount category bins
amount_raised_bin_matrix = []

for firm in firms:
  row = {"Firm": firm}
  for b in amount_raised_bins:
   num = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
   row[b] = num
  amount_raised_bin_matrix.append(row)

amount_raised_matrix_df = pd.DataFrame(amount_raised_bin_matrix)

#GAFAM firm similarity scores for employee count category bins
employee_bin_matrix = []

for firm in firms:
  row = {"Firm": firm}
  for b in number_of_employees_bins:
   num = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
   row[b] = num
  employee_bin_matrix.append(row)

employee_matrix_df = pd.DataFrame(employee_bin_matrix)

#Main Dashboard Navigation, users switch between different analytical views
st.title("Mapping AI Industry Structure Through Mergers and Acquisitions")
view = st.radio("Select View", ["Acquisitions", "AI Technical Stack Data", "Bin Data", "Charts", "Graphs"])

#Display raw acquisition data in the dashboard

if view == "Acquisitions":
  # Select firm to analyze acquisitions
  st.subheader("Raw Acquisition Data Overview by AI Category")
  selected_firm = st.selectbox("Select Company", firms)
  acquisitions = []

  #Find acquisition relationships of the selected firm
  for x, row in triples_df.iterrows():
    if row["head"] == selected_firm and row["relation"] == "ACQUIRES":
      acquired = row["tail"]

      #Find AI category of acquired company
      for y, r in triples_df.iterrows():
        if r["head"] == acquired and r["relation"] == "IS_A":
          acquisitions.append({"Acquiring Company": selected_firm, "Acquired Company": acquired, "AI Category": r['tail']})

  acquired_df = pd.DataFrame(acquisitions)
  st.dataframe(acquired_df)

elif view == "AI Technical Stack Data":
  st.subheader("Firm and AI Category Similarity Scores")

  #Display the matrix for GAFAM firm similarity scores for AI capability categories (DATA, COMPUTE, MODELING, APPLICATIONS)
  st.dataframe(cat_matrix_df)

elif view == "Bin Data":
  st.subheader("Firm and Bin Similarity Scores")
  selected_firm = st.selectbox("Select Company", firms)

  #Filter similarity tables that have already been computed
  employee_scores = employee_matrix_df[employee_matrix_df["Firm"] == selected_firm]
  deal_scores = deal_matrix_df[deal_matrix_df["Firm"] == selected_firm]
  amount_raised_scores = amount_raised_matrix_df[amount_raised_matrix_df["Firm"] == selected_firm]

  #Display matrices
  st.write("Number of Employees Category")
  st.dataframe(employee_scores)

  st.write("Deal Value Category")
  st.dataframe(deal_scores)

  st.write("Amount Raised Category")
  st.dataframe(amount_raised_scores)

elif view == "Charts":
  st.subheader("Cosine Similarity of AI Acquisition Strategies by Company")
  firm = st.selectbox("Pick a firm", firms)

  #Compute similarity score to size bins
  deal_scores = {}
  for b in deal_bins:
    if b in model.wv and firm in model.wv:
      score = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
      deal_scores[b] = score

  amount_raised_scores = {}
  for b in amount_raised_bins:
    if b in model.wv and firm in model.wv:
      score = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
      amount_raised_scores[b] = score

  employee_count_scores = {}
  for b in number_of_employees_bins:
    if b in model.wv and firm in model.wv:
      score = cosine_similarity([model.wv[firm]], [model.wv[b]])[0][0]
      employee_count_scores[b] = score

  #Compute similarity score to AI categories
  cat_scores = {}
  for c in categories:
    if c in model.wv:
      score = cosine_similarity([model.wv[firm]], [model.wv[c]])[0][0]
      cat_scores[c] = score

  #Convert from dictionaries to dataframes for plotting
  deal_bin_df = pd.DataFrame({"Category": list(deal_scores.keys()), "Similarity": list(deal_scores.values())})
  amount_raised_bin_df = pd.DataFrame({"Category": list(amount_raised_scores.keys()), "Similarity": list(amount_raised_scores.values())})
  employee_count_bin_df = pd.DataFrame({"Category": list(employee_count_scores.keys()), "Similarity": list(employee_count_scores.values())})
  cat_df = pd.DataFrame({"Category": list(cat_scores.keys()), "Similarity": list(cat_scores.values())})

  #Display two side by side charts
  row1_col1, row1_col2 = st.columns(2)
  row2_col1, row2_col2 = st.columns(2)

  with row1_col1:
    st.subheader("AI Capability Categories")
    st.bar_chart(cat_df, x="Category", y="Similarity")

  with row1_col2:
    st.subheader("Deal Size Categories")
    st.bar_chart(deal_bin_df, x="Category", y="Similarity")

  with row2_col1:
    st.subheader("Amount Raised Categories")
    st.bar_chart(amount_raised_bin_df, x="Category", y="Similarity")

  with row2_col2:
    st.subheader("Employee Size Categories")
    st.bar_chart(employee_count_bin_df, x="Category", y="Similarity")

elif view == "Graphs":
  st.subheader("Company-Level Knowledge Graphs")

  selected_company = st.selectbox("Pick a firm", firms)

  #Toggle filters for graph visualization
  show_ai_category = st.checkbox("AI Category", True)
  show_employees = st.checkbox("Employee Categories", True)
  show_deals = st.checkbox("Deal Value Categories", True)
  show_raised = st.checkbox("Amount Raised Categories", True)

  #Build filtered graph
  G = build_graph(triples_df, selected_company, show_ai_category, show_deals, show_raised, show_employees)

  #Draw graph
  fig, ax = plt.subplots(figsize=(10, 8))
  pos = nx.spring_layout(G, seed=42)

  nx.draw_networkx_nodes(G, pos, ax=ax)
  nx.draw_networkx_edges(G, pos, alpha=0.4, ax=ax)
  nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)

  ax.set_axis_off()
  st.pyplot(fig)
