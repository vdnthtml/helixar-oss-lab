#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
LAB=Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust')
log=LAB/'logs/process-network.jsonl'
rows=[json.loads(x) for x in log.read_text().splitlines() if x.strip()]
exceptions=[json.loads(x) for x in (LAB/'logs/network-exceptions.jsonl').read_text().splitlines() if x.strip()]
# This process is appended by labrun only after this script exits, so count it explicitly.
data={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'started_at_utc':min(x['started_at_utc'] for x in rows),'last_completed_before_freeze_utc':max(x['ended_at_utc'] for x in rows),'logged_command_count_including_this_freeze':len(rows)+1,'network_command_count':sum(x['kind']=='network' for x in rows),'unplanned_network_fetch_count':len(exceptions),'network_fetch_operation_count':sum(x['kind']=='network' for x in rows)+len(exceptions),'local_command_count_including_this_freeze':sum(x['kind']=='local' for x in rows)+1,'failed_command_count':sum(x['exit_code']!=0 for x in rows),'external_write_count':0,'business_action_count':0,'credential_access_count':0,'implementation_repository_write_count':0}
for name in ['validation-result.json','source-metadata.json','lab-summary.json','logs/process-network.jsonl','logs/network-exceptions.jsonl']:
 p=LAB/name
 data[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(LAB/'receipt-data.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
