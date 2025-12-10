from utils.drug_info_fetcher import DrugInfoFetcher
import requests

fetcher = DrugInfoFetcher()

# Test with Aspirin
rxcui = fetcher.get_rxcui('Aspirin')
print(f'RxCUI for Aspirin: {rxcui}')

# Test RxNav API directly with the new endpoint
resp = requests.get(f'https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui}')
print(f'\nAPI Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    print(f'Response keys: {list(data.keys())}')
    
    if 'fullInteractionTypeGroup' in data:
        groups = data['fullInteractionTypeGroup']
        print(f'Interaction groups: {len(groups)}')
        if groups:
            print(f'\nFirst group keys: {list(groups[0].keys())}')
            print(f'Source: {groups[0].get("sourceName")}')
    else:
        print('No fullInteractionTypeGroup in response')
else:
    print(f'Error response: {resp.text}')

# Test our function
print('\n--- Testing get_drug_interactions ---')
interactions = fetcher.get_drug_interactions('Aspirin')
print(f'Found {len(interactions)} interactions')
for i, interaction in enumerate(interactions[:3], 1):
    print(f"{i}. {interaction['drug']}: {interaction['description'][:100] if interaction['description'] else 'No description'}...")
