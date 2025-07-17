# CRITICAL RAILWAY DEPLOYMENT FIX

## 🚨 ALWAYS USE FULL COMMIT HASH FOR RAILWAY DEPLOYMENTS

### Problem:
Railway deployment fails with error:
```
Failed to fetch specific commit: couldn't find remote ref "b7103bb"
```

### Solution:
**ALWAYS use the FULL Git commit hash, NOT the short version!**

❌ **WRONG**: `b7103bb` (short hash)
✅ **CORRECT**: `b7103bbef93dc2bf505067fde65c1093bb32572c` (full hash)

### How to Get Full Hash:
```bash
# Get full hash for a commit
git rev-parse b7103bb

# Or use git log
git log --format="%H" -n 1
```

### Example Deployment Command:
```javascript
mcp__railway__deployment_trigger({
  projectId: "b4887af6-4cdb-402d-9287-aabb19804db8",
  serviceId: "df81c750-3b09-457a-a0bb-18f23167be07", 
  environmentId: "a928b0f7-0b28-4746-98d2-8c1fc2227df4",
  commitSha: "b7103bbef93dc2bf505067fde65c1093bb32572c" // FULL HASH!
})
```

## Remember This Forever!
This fix resolved multiple failed deployments on 7/17/2025. Railway's API requires the complete SHA-1 hash to fetch commits from GitHub.

---
*Created: 7/17/2025 - COMMIT TO MEMORY*