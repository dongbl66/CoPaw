import urllib.request, json, time, http.client

BASE = "http://localhost:8000/api/agents/ai-bid-master/bid-projects"

# 1. Create project
req = urllib.request.Request(BASE, data=json.dumps({
    "name":"智慧城市云平台技术服务公开采购项目",
    "project_type":"服务类",
    "description":"AI辅助评审系统Demo测试",
    "bid_opening_time":"2025-06-15T14:00:00"
}).encode(), headers={"Content-Type":"application/json"}, method="POST")
resp = urllib.request.urlopen(req)
proj = json.loads(resp.read())
pid = proj["id"]
print(f"1. 项目创建: {pid} [{proj['status']}]")

# 2. Rule extraction
req2 = urllib.request.Request(f"{BASE}/{pid}/rule-extraction-jobs", method="POST")
resp2 = urllib.request.urlopen(req2)
rjob = json.loads(resp2.read())
rid = rjob["job_id"]
print(f"2. 规则提取任务: {rid} [{rjob['status']}]")

time.sleep(3)

resp3 = urllib.request.urlopen(f"{BASE}/{pid}/rule-extraction-jobs/{rid}")
rjob2 = json.loads(resp3.read())
print(f"   状态: {rjob2['status']}")

resp4 = urllib.request.urlopen(f"{BASE}/{pid}/review-rules")
rules = json.loads(resp4.read())
print(f"3. 评审规则: {len(rules['rules'])}条")

# 4. Register supplier (mock) - use urllib instead
import urllib.parse
data = urllib.parse.urlencode({"supplier_name": "星辰科技有限公司"}).encode()
req_s = urllib.request.Request(
    f"{BASE}/{pid}/suppliers?mock=true",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST"
)
resp5 = urllib.request.urlopen(req_s)
supp = json.loads(resp5.read())
sid = supp["id"]
print(f"4. 供应商登记: {sid} [{supp['status']}]")

time.sleep(2)

# 5. Start review
req6 = urllib.request.Request(f"{BASE}/{pid}/suppliers/{sid}/review-jobs", method="POST")
resp6 = urllib.request.urlopen(req6)
rvjob = json.loads(resp6.read())
rvid = rvjob["job_id"]
print(f"5. 评审任务: {rvid} [{rvjob['status']}]")

time.sleep(5)

resp7 = urllib.request.urlopen(f"{BASE}/{pid}/suppliers/{sid}/review-jobs/{rvid}")
rvjob2 = json.loads(resp7.read())
print(f"   评审状态: {rvjob2['status']}")

# 6. Review summary
resp8 = urllib.request.urlopen(f"{BASE}/{pid}/suppliers/{sid}/review-summary")
summary = json.loads(resp8.read())
print(f"6. 评审总览: {summary['final_conclusion']} ({summary['item_count']}项, 置信度: {summary['confidence']})")

# 7. Generate report
req9 = urllib.request.Request(f"{BASE}/{pid}/suppliers/{sid}/report-jobs", method="POST")
resp9 = urllib.request.urlopen(req9)
rpjob = json.loads(resp9.read())
rpid = rpjob["job_id"]
print(f"7. 报告任务: {rpid}")

time.sleep(3)

resp10 = urllib.request.urlopen(f"{BASE}/{pid}/suppliers/{sid}/report-jobs/{rpid}")
rpjob2 = json.loads(resp10.read())
print(f"   报告状态: {rpjob2['status']}")

resp11 = urllib.request.urlopen(f"{BASE}/{pid}/suppliers/{sid}/report-result")
report = json.loads(resp11.read())
print(f"8. 报告: {report['final_conclusion']} (通过{report['summary']['passed']}/{report['summary']['total_items']}项)")

print("\n全部流程测试通过!")
