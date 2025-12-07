Face Rig Generator
---

Import the face-rig from a blend file.
User fits the bones to the face.
User generates weight-maps.
User runs the generator (a separate operator from generating the base rig).

The generator should:

* Detect all bone chains.
* Create bendy bone handles at each bone-head position.
* From the handles, create bendy bone chains by parenting the bone in front of the handle. Handles should be parented to DEF-Head by default.
* No renaming should take place since the bones are already prefixed.
* Remove red bones and weight-maps prefixed with `_TMP_`
    - these bones and weight-maps are intended to prevent the face weight-maps from bleeding into the rest of the figure.
    
Optional:
* Generate an inner mouth rig (Jaw and Teeth Upper/Lower)
    - if selected, certain lower face control bones should be parented to the jaw bone
* Generate a tongue rig