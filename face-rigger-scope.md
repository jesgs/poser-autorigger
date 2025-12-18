Face Rig Generator
---
This is a face rig that uses bendy bone chains, similar to CloudRig. If I were using CloudRig, these bones would have the Face: Grid type.
A standard bendy bone chain consist of a:
1. Start Handle bone
2. Bendy bone (this bone has its segment set higher than 1)
3. End Handle bone, which is the Start Handle bone of the next bendy bone.

### Standard Bendy Bone Chain Construction
1. Bendy bone is parented to its start handle.
2. Set bendy bone's start handle to its parent.
3. Set bendy bone's end handle to the handle on the next bendy bone's head.
4. Bendy bone has a STRETCH_TO constraint pointing at the end handle.
5. Repeat steps 1 through 4 until the end of the chain is reached.
6. Create a new bone at the tail of the last bone in the chain.
7. Set the last bone's end handle to the bone we just created, and add a STRETCH_TO constraint referencing the end handle.

### Converting bone chains to bendy bone chains
1. Detect all bone chains.
2. Create a dictionary of each of these bone chains using the name of the first bone in the chain, with number stripped from the name. Example:
    ```
    {
        'Bone_Name.L' : {
            'Bone_Name1.L',
            'Bone_Name2.L',
            ...
    }
    ```
3. Bendy bone chains are created like this:
    1. Once chains are detected, clear all parents.     
    2. Change the settings on each bone to:
        - Segments: 10 (should actually be configurable by the user but default to 10 for now)
        - Bone Size X and Z: 0.00025
        - Vertex Mapping: CURVED
        - Start Handle: TANGENT
        - End Handle: TANGENT    
    4. Create new bones at the head of each bone as well as a new bone at the tail of the last bone in the chain.
        - These bones should be named "Tweak-{Main_Bone_Chain_Name}{#}{.L|.R}"
    5. Follow steps 1 through 4 as outlined in **Standard Bendy Bone Chain Construction**
    6. For the final bendy bone, follow steps 6 and 7 in **Standard Bendy Bone Chain Construction**

