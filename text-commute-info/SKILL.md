---
name: text-commute-info
description: Gets your commute time and route options, then texts you the details
compatibility: Created for Zo Computer
metadata:
  author: ian.zo.computer
  category: Community
  display-name: Text commute travel time and route
  emoji: 🚏
---

# Prerequisites

- [ ] User should have their phone number added

---

# Inputs

- Origin
- Destination
- Travel mode (driving, transit, walking, bicycling, two-wheeler)

---

# Protocol

1. Build the correct URL for the Google Maps API URL as following:\
   `https://www.google.com/maps/dir/?api=1&origin=<ORIGIN>&destination=<DESTINATION>&travelmode=<TRAVELMODE>` where `<ORIGIN>` is the user's provided origin, `<DESTINATION>` is the user's provided destination, and `<TRAVELMODE>` is the user's requested travel mode.
2. Use `tool open_webpage` to navigate to the URL you constructed, then use `tool view_webpage` to inspect the route options.
3. If the user explicitly asked for a text message, use `tool send_sms_to_user` to relay the information from the page, giving them the top two travel options with their estimated travel time. If transit, explicitly list every train or bus line and transfer used in a route (e.g. Take the M, then G, then L). Also include the URL so the user can see the route on Google Maps. If they did not ask for a text, reply in the current chat instead.
4. Inform the user that they can repeat this workflow as a `Rule` or scheduled `Agent`. For example, a `Rule` could be

```markdown
When I text you asking for commute info, use `prompt Prompts/text-commute-info.prompt.md` but IGNORE step 4.
```

and a scheduled `Agent` could be set to run daily in the morning so that the user can be prepared for going to work or school. If the user explicitly wants this, use `tool create_agent` with SMS delivery and instruction:

```markdown
Run `prompt Prompts/text-commute-info.prompt.md` with origin <ORIGIN>, destination <DESTINATION>, and travel mode <TRAVELMODE>, but IGNORE step 4
```
