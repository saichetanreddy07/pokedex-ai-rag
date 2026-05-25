from rag.retriever import retrieve_documents

query = "electric mouse pokemon"

results = retrieve_documents(query)

print("\nQUERY:")
print(query)

print("\nRETRIEVED DOCUMENTS:")
print("=" * 50)

for doc in results["documents"][0]:

    print(doc)
    print("\n" + "=" * 50)