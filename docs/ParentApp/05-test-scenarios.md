---
project: ForKhatri
artifact: Parent Application Test Scenarios
step: 5
status: Ready for Review
---

# Parent Application Test Scenarios

| ID | Scenario | Expected result |
|---|---|---|
| TS01 | Open the parent webpage with no stored session | Shared ForKhatri signed-out entry state renders. |
| TS02 | Open with a valid member session | Parent home renders without a module login. |
| TS03 | Open the Modules section | All seven planned module cards render with correct status. |
| TS04 | Select an available module | Parent context changes or module route opens without a second login. |
| TS05 | Select a planned module | Informational planned state appears; the shell remains usable. |
| TS06 | Switch between two module contexts | Shared member context and session remain intact. |
| TS07 | Open Notifications | Shared notification surface opens and identifies source modules. |
| TS08 | Open the member menu | Parent account/settings actions are available. |
| TS09 | Use keyboard navigation | All interactive controls are reachable and visibly focused. |
| TS10 | Use a narrow viewport | No horizontal overflow; navigation remains usable. |
| TS11 | Enable reduced motion | Non-essential transitions are removed or reduced. |
| TS12 | Simulate unavailable module data | Stable fallback appears without blanking the shell. |
| TS13 | Inspect module entry markup | No module-specific credential or second-login action exists. |
| TS14 | Check semantic structure | One main heading, landmarks, accessible names, and logical heading order exist. |
| TS15 | Check visual status contrast | Available/planned/status labels meet the intended contrast baseline. |

