"""Full integration test for AI Review Demo (Skills + Review Flow)"""
import urllib.request, json, time, urllib.parse, os

BASE = "http://localhost:8000/api/agents/ai-bid-master/bid-projects"
SKILL_API = "http://localhost:8000/api/skills"

def req(url, method="GET", data=None, headers=None):
    h = headers or {}
    if data and isinstance(data, dict):
        data = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    resp = urllib.request.urlopen(r)
    return json.loads(resp.read())

# ── Skill Tests ──
print("=== Skill Management ===")

skills = req(SKILL_API)
print(f"  ✅ List: {len(skills)} skills registered: {[s['id'] for s in skills]}")

meta = req(f"{SKILL_API}/ai-bid-auth")
print(f"  ✅ Meta: {meta['name']} - {len(meta['capabilities'])} capabilities")

md = req(f"{SKILL_API}/ai-bid-auth/skill-md")
print(f"  ✅ SKILL.md: {len(md['content'])} chars, starts with: {md['content'][:50].strip()}")

for sid in ["ai-bid-auth", "ai-bid-compliance", "ai-bid-audit", "ai-bid-master"]:
    skmd = f"demo_data/skills/{sid}/SKILL.md"
    skjson = f"demo_data/skills/{sid}/skill.json"
    assert os.path.exists(skmd), f"Missing {skmd}"
    assert os.path.exists(skjson), f"Missing {skjson}"
print(f"  ✅ Files: All 4 skills have SKILL.md + skill.json on disk")

# ── Review Flow ──
print("\n=== Review Flow ===")

# Create project
proj = req(BASE, "POST", {"name": "智慧城市云平台技术服务", "project_type": "服务类"})
pid = proj["id"]
print(f"  ✅ Create project: {pid} [{proj['status']}]")

# Rule extraction
time.sleep(1)
rjob = req(f"{BASE}/{pid}/rule-extraction-jobs", "POST")
rid = rjob["job_id"]
time.sleep(3)
rstat = req(f"{BASE}/{pid}/rule-extraction-jobs/{rid}")
assert rstat["status"] == "succeeded", f"Rule status: {rstat['status']}"
print(f"  ✅ Rule extraction: succeeded")

# Register supplier
data = urllib.parse.urlencode({"supplier_name": "星辰科技有限公司"}).encode()
supp = req(f"{BASE}/{pid}/suppliers?mock=true", "POST", data, {"Content-Type": "application/x-www-form-urlencoded"})
sid = supp["id"]
time.sleep(2)
print(f"  ✅ Register supplier: {sid}")

# Start review
time.sleep(1)
rvjob = req(f"{BASE}/{pid}/suppliers/{sid}/review-jobs", "POST")
rvid = rvjob["job_id"]
time.sleep(6)
rvstat = req(f"{BASE}/{pid}/suppliers/{sid}/review-jobs/{rvid}")
assert rvstat["status"] == "succeeded", f"Review status: {rvstat['status']}"
print(f"  ✅ Review: succeeded")

# Summary
summary = req(f"{BASE}/{pid}/suppliers/{sid}/review-summary")
print(f"  ✅ Summary: {summary['final_conclusion']} ({summary['item_count']} items, {summary['confidence']})")

print(f"\n🎉 All tests passed!")
