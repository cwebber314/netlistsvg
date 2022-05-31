"""Convert CIM-XML model to JSON netlist. 
"""
from xml.dom import minidom
import pandas as pd
import sys
import hashlib
import pdb
import json

file = minidom.parse('sample_nb.xml')

def cleanrdfid(rdfid):
    rdfid = rdfid.replace('_', '')
    rdfid = rdfid.replace('#', '')
    return rdfid

def _Terminal():
    terminals = file.getElementsByTagName('cim:Terminal')
    rows = []
    for terminal in terminals:
        dd = {}
        dd['Terminal_rdfID'] = cleanrdfid(terminal.attributes['rdf:ID'].value)
        dd['ConductingEquipment_rdfID'] = cleanrdfid(terminal.getElementsByTagName('cim:Terminal.ConductingEquipment')[0].attributes['rdf:resource'].value)
        dd['ConnectivityNode_rdfID'] = cleanrdfid(terminal.getElementsByTagName('cim:Terminal.ConnectivityNode')[0].attributes['rdf:resource'].value)
        # if dd['Terminal_rdfID'] == '69230818-db84-11ec-b339-223941000548':
            # pdb.set_trace()
        try:
            dd['sequenceNumber'] = terminal.getElementsByTagName('cim:ACDCTerminal.sequenceNumber')[0].childNodes[0].data.strip()
        except IndexError:
            pass
        dd['Terminal_name'] = terminal.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        rows.append(dd.copy())
    df_terminal = pd.DataFrame.from_dict(rows)
    return df_terminal

def ConnectivityNode():
    nodes = file.getElementsByTagName('cim:ConnectivityNode')
    rows = []
    for node in nodes:
        dd = {}
        dd['ConnectivityNode_rdfID'] = cleanrdfid(node.attributes['rdf:ID'].value)
        dd['ConnectivityNode_name'] = node.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        dd['ConnectivityNodeContainer'] = cleanrdfid(node.getElementsByTagName('cim:ConnectivityNode.ConnectivityNodeContainer')[0].attributes['rdf:resource'].value)
        rows.append(dd.copy())
    df_node = pd.DataFrame.from_dict(rows)
    return df_node

def Terminal():
    t = _Terminal()
    cn = ConnectivityNode()
    df = pd.merge(t, cn, how='left', on='ConnectivityNode_rdfID')
    return df

def _Disconnector():
    # Get switch
    disconnectors = file.getElementsByTagName('cim:Disconnector')
    rows = []
    for disconnector in disconnectors:
        dd = {}
        dd['Disconnector_rdfID'] = cleanrdfid(disconnector.attributes['rdf:ID'].value)
        try:
            dd['Disconnector_name'] = disconnector.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        except IndexError:
            pass
        dd['EquipmentContainer_rdfID'] = cleanrdfid(disconnector.getElementsByTagName('cim:Equipment.EquipmentContainer')[0].attributes['rdf:resource'].value)
        dd['Disconnector_description'] = disconnector.getElementsByTagName('cim:IdentifiedObject.description')[0].childNodes[0].data.strip()
        rows.append(dd.copy())
    df_disconnector = pd.DataFrame.from_dict(rows)
    return df_disconnector

def _Breaker():
    # Get breaker
    breakers = file.getElementsByTagName('cim:Breaker')
    rows = []
    for breaker in breakers:
        dd = {}
        dd['Breaker_rdfID'] = cleanrdfid(breaker.attributes['rdf:ID'].value)
        try:
            dd['Breaker_name'] = breaker.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        except IndexError:
            pass
        dd['EquipmentContainer_rdfID'] = cleanrdfid(breaker.getElementsByTagName('cim:Equipment.EquipmentContainer')[0].attributes['rdf:resource'].value)
        dd['Breaker_description'] = breaker.getElementsByTagName('cim:IdentifiedObject.description')[0].childNodes[0].data.strip()
        rows.append(dd.copy())
    df_breaker = pd.DataFrame.from_dict(rows)
    return df_breaker

def Breaker():
    breaker = _Breaker()
    terminal = Terminal()
    
    # Since there's two temrinals there will double the number of rows
    bterm = pd.merge(terminal, breaker, how='inner', left_on='ConductingEquipment_rdfID', right_on='Breaker_rdfID')
    bterm1 = bterm[bterm['sequenceNumber'] == '1']
    bterm1 = bterm1[['ConductingEquipment_rdfID', 'ConnectivityNode_rdfID']]
    bterm1 = bterm1.rename(columns={'ConnectivityNode_rdfID': 'ConnectivityNode_rdfID_1', 
                                    'ConductingEquipment_rdfID': 'Breaker_rdfID'})

    bterm2 = bterm[bterm['sequenceNumber'] == '2']
    bterm2 = bterm2[['ConductingEquipment_rdfID', 'ConnectivityNode_rdfID']]
    bterm2 = bterm2.rename(columns={'ConnectivityNode_rdfID': 'ConnectivityNode_rdfID_2',
                                    'ConductingEquipment_rdfID': 'Breaker_rdfID'})

    df = pd.merge(breaker, bterm1, on='Breaker_rdfID')
    df = pd.merge(df, bterm2, on='Breaker_rdfID')
    return df

def Disconnector():
    switch = _Disconnector()
    terminal = Terminal()
    
    # Since there's two temrinals there will double the number of rows
    bterm = pd.merge(terminal, switch, how='inner', left_on='ConductingEquipment_rdfID', right_on='Disconnector_rdfID')
    bterm1 = bterm[bterm['sequenceNumber'] == '1']
    bterm1 = bterm1[['ConductingEquipment_rdfID', 'ConnectivityNode_rdfID']]
    bterm1 = bterm1.rename(columns={'ConnectivityNode_rdfID': 'ConnectivityNode_rdfID_1', 
                                    'ConductingEquipment_rdfID': 'Disconnector_rdfID'})

    bterm2 = bterm[bterm['sequenceNumber'] == '2']
    bterm2 = bterm2[['ConductingEquipment_rdfID', 'ConnectivityNode_rdfID']]
    bterm2 = bterm2.rename(columns={'ConnectivityNode_rdfID': 'ConnectivityNode_rdfID_2',
                                    'ConductingEquipment_rdfID': 'Disconnector_rdfID'})

    df = pd.merge(switch, bterm1, on='Disconnector_rdfID')
    df = pd.merge(df, bterm2, on='Disconnector_rdfID')
    return df

def _ConformLoad():
    # Get Load
    loads = file.getElementsByTagName('cim:ConformLoad')
    rows = []
    for load in loads:
        dd = {}
        dd['ConformLoad_rdfID'] = cleanrdfid(load.attributes['rdf:ID'].value)
        dd['ConformLoad_name'] = load.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        dd['pfixed'] = load.getElementsByTagName('cim:EnergyConsumer.pfixed')[0].childNodes[0].data.strip()
        dd['qfixed'] = load.getElementsByTagName('cim:EnergyConsumer.qfixed')[0].childNodes[0].data.strip()
        dd['EquipmentContainer_rdfID'] = cleanrdfid(load.getElementsByTagName('cim:Equipment.EquipmentContainer')[0].attributes['rdf:resource'].value)
        rows.append(dd.copy())
    df_load = pd.DataFrame.from_dict(rows)
    return df_load

def _ACLineSegment():
# Get ACLineSegment
    branches = file.getElementsByTagName('cim:ACLineSegment')
    rows = []
    for branch in branches:
        dd = {}
        dd['ACLineSegment_rdfID'] = cleanrdfid(branch.attributes['rdf:ID'].value)
        dd['ACLineSegment_name'] = branch.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        dd['r'] = branch.getElementsByTagName('cim:ACLineSegment.r')[0].childNodes[0].data.strip()
        dd['x'] = branch.getElementsByTagName('cim:ACLineSegment.x')[0].childNodes[0].data.strip()
        rows.append(dd.copy())
    df_branch = pd.DataFrame.from_dict(rows)
    return df_branch

def GeneratingUnit():
    # Get Generator
    gens = file.getElementsByTagName('cim:GeneratingUnit')
    rows = []
    for gen in gens:
        dd = {}
        dd['GeneratingUnit_rdfID'] = cleanrdfid(gen.attributes['rdf:ID'].value)
        dd['nominalP'] = gen.getElementsByTagName('cim:GeneratingUnit.nominalP')[0].childNodes[0].data.strip()
        dd['GeneratingUnit_name'] = gen.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        dd['EquipmentContainer_rdfID'] = cleanrdfid(gen.getElementsByTagName('cim:Equipment.EquipmentContainer')[0].attributes['rdf:resource'].value)
        rows.append(dd.copy())
    df_gens = pd.DataFrame.from_dict(rows)

def LinearShuntCompensator():
    # Get Shunt
    shunts = file.getElementsByTagName('cim:LinearShuntCompensator')
    rows = []
    for shunt in shunts:
        dd = {}
        dd['LinearShuntCompensator_rdfID'] = cleanrdfid(shunt.attributes['rdf:ID'].value)
        dd['LinearShuntCompensator_name'] = shunt.getElementsByTagName('cim:IdentifiedObject.name')[0].childNodes[0].data.strip()
        dd['bPerSection'] = shunt.getElementsByTagName('cim:LinearShuntCompensator.bPerSection')[0].childNodes[0].data.strip()
        dd['EquipmentContainer_rdfID'] = cleanrdfid(shunt.getElementsByTagName('cim:Equipment.EquipmentContainer')[0].attributes['rdf:resource'].value)
        rows.append(dd.copy())
    df_shunt = pd.DataFrame.from_dict(rows)
    return df_shunt

def Substation():
    return

def PowerTransformer():
    return

def VoltageLevel():
    return

# Only plot one voltage level - substation makes more sense, but this is easier.

# VoltageLevel SUB_230 (main-transfer with bus tie?)
#vl = '692303a3-db84-11ec-b339-223941000548'

# VoltageLevel EAS_500 (not sure)
# vl = '6923037a-db84-11ec-b339-223941000548'

# VL for URB_230
#vl = '692303d6-db84-11ec-b339-223941000548'

# VL for WES_500 (6 breaker ring)
vl = '692304ae-db84-11ec-b339-223941000548'

# get nodes in voltage level ConnectivityNodeContainer
node = ConnectivityNode()
node = node[node['ConnectivityNodeContainer'] == vl]

breaker = Breaker()
m1 = breaker['ConnectivityNode_rdfID_1'].isin(node['ConnectivityNode_rdfID'])
m2 = breaker['ConnectivityNode_rdfID_2'].isin(node['ConnectivityNode_rdfID'])
breaker = breaker[m1 | m2]

switch = Disconnector()
m1 = switch['ConnectivityNode_rdfID_1'].isin(node['ConnectivityNode_rdfID'])
m2 = switch['ConnectivityNode_rdfID_2'].isin(node['ConnectivityNode_rdfID'])
switch = switch[m1 | m2]

net = {'modules': {'module_name': {'ports': {}, 'cells': {}} }}

# sys.exit()
cells = []

def hash(val):
    hashed = int(hashlib.sha1(val.encode("UTF-8")).hexdigest()[:5], 16)
    return hashed
    
for i, row in breaker.iterrows():
    # pdb.set_trace()
    cell = {}
    if 'Breaker_name' in row.keys():
        key = row['Breaker_name']
    else:
        key = row['Breaker_description']
        # key = hash(row['Breaker_rdfID'])

    dd = {}
    dd['type'] = 'breaker_v'
    dd['connections'] = {
        "A": [hash(row['ConnectivityNode_rdfID_1'])],
        "B": [hash(row['ConnectivityNode_rdfID_2'])]
    }
    net['modules']['module_name']['cells'][key] = dd

for i, row in switch.iterrows():
    # pdb.set_trace()
    cell = {}
    if 'Breaker_name' in row.keys():
        key = row['Disconnector_name']
    else:
        # key = hash(row['Disconnector_rdfID'])
        key = row['Disconnector_description']

    dd = {}
    dd['type'] = 'switch_v'
    dd['connections'] = {
        "A": [hash(row['ConnectivityNode_rdfID_1'])],
        "B": [hash(row['ConnectivityNode_rdfID_2'])]
    }
    net['modules']['module_name']['cells'][key] = dd

with open('cim_test_4.json', 'w') as f:
    s = json.dumps(net, indent=2)
    f.write(s)