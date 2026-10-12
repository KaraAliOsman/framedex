"""Explicit measurement authority for manufacturing fixtures predating D07.

These fixtures declare a synthetic direct-product mounting with zero allowance.
They are never a production default or a bypass of the release gate.
"""

from dekopen_engine.mounting import MountingRule, OpeningSurvey, derive_fabrication
from pricing.repository import json_text, one, rows
from projects.extras import extra_backend
from projects.mounting import append_measurement
from projects.service import position_row, position_public, project_row


def confirm_fixture_measurements(org,position_id):
    position=position_row(org,position_id)
    design=position_public(position)['design']
    side={name:'0' for name in ('clearance_mm','frame_mm','extension_mm','overlap_mm')}
    rule=MountingRule.model_validate({'code':'FIXTURE_DIRECT','name':'Medida de fabricación directa · DEMO',
        'kind':'IN_OPENING','source':'Ensayo de producción anterior a D07; vano nominal igual a producto, sin holgura',
        'synthetic':True,'tolerance_mm':'0',**{s:side for s in ('left','right','top','bottom')},'extras':[]})
    with extra_backend():
        if not rows("SELECT code FROM mounting_rules WHERE org_id=%s AND system_id=%s AND code='FIXTURE_DIRECT'",[org,design['system_id']]):
            one("INSERT INTO mounting_rules(org_id,system_id,code,revision,rule,actor_id,reason) VALUES(%s,%s,%s,1,%s::jsonb,"
                "(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid,%s) RETURNING code",
                [org,design['system_id'],rule.code,json_text(rule.model_dump(mode='json')),'Declaración explícita del fixture'])
    tree=design['parametric_tree']
    modules=tree['assembly']['modules'] if tree.get('version')=='product-v2' else [
        {'id':None,'width_mm':design['nominal_width_mm'],'height_mm':design['nominal_height_mm']}]
    evidence=[]
    for module in modules:
        survey=OpeningSurvey.model_validate({'module_id':module['id'],'rule_code':rule.code,'rule_revision':1,
            'widths_mm':[module['width_mm']],'heights_mm':[module['height_mm']],'wall':'CONCRETE','origin':'SITE'})
        evidence.append({'survey':survey.model_dump(mode='json'),'rule':rule.model_dump(mode='json'),
                         'result':derive_fabrication(survey,rule).model_dump(mode='json')})
    revision=project_row(org,position['project_id'])['current_revision']
    append_measurement(org,position,revision,evidence,'CONFIRMED','Responsable del fixture verificó dimensiones nominales directas')
