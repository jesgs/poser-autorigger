# Poser Autorigger for Blender

An autorigger for Poser characters imported as FBX files.

This auto-rigging tool is geared specifically towards FBX imported figures that already have an existing base armature. This tool takes that existing armature and automates the setup of IK/FK chains, bone collections, and bone widgets.

**Under development—Use at your own risk**

## **Workflow Summary**

1. User imports their FBX Poser character to Blender.
2. Runs auto-rigger script/addon.
3. Addon detects the armature, generates required IK/FK chains, creates controls, and assigns custom shapes.
4. Rig is ready for animation with standard Blender controls.

## TODOs

- [x] Determine if mesh correction code should be removed or expanded. This code is actually part of [Poser Tools](https://github.com/jesgs/poser-tools).
  - Move to Poser Tools. We can bring it back later or merge the two add-ons.
- [ ] Rig UI panel ideas: built-in but still provides support for [Bone Manager](https://fin.gumroad.com/l/STdb) and [Rig UI](https://superhivemarket.com/products/rig-ui)
- [ ] Test against other Poser figures (Daz3d Millennium 4 figures, La Femme and Le Homme, AnimeDoll, etc.)

## Base Feature Set for Poser FBX Auto-Rigger in Blender

### 1. IK/FK Chain Creation
- **Limbs (Arms & Legs):**
  - Detect existing limb bones (shoulder, upper arm, forearm, hand, thigh, shin, foot).
  - [x] Generate IK chains for arms and legs.
  - [x] Generate FK chains for arms and legs.
- **Fingers:**
  - [x] Detect finger bones.
  - [x] Create FK controls for each finger.
  - [x] Add IK controls for each finger, including thumb.

- **Spine:**
  - [x] Detect spine bones.
  - [x] Create FK controls along the spine.
  - [x] Create IK controls along the spine.

### 2. Foot Roll Control
- **Foot Rig Features:**
  - [x] Add foot roll controller (using a custom bone or empty).
  - [ ] Setup constraints for toe bend, heel lift, ball roll, etc.
  - [ ] Automatic foot banking (side-to-side roll).

### 3. Constraints Setup
- **Rig Constraints:**
  - [x] Add necessary constraints for all IK and FK chains (IK, Copy Rotation, Limit Rotation, etc.).
  - [x] Ensure pole targets are generated and positioned correctly for knees/elbows.
  - [x] Setup drivers or custom properties for easy switching and control.

### 4. Control Custom-Shapes
- **Custom Bone Shapes:**
  - [x] Assign custom shapes to each main control (IK handles, FK controls, foot roll, pole targets).

### 5. User Interface (Optional, but recommended for usability)
- **Rig UI Panel:**
  - [ ] Add a custom sidebar panel in Blender for rig controls (IK/FK switch, foot roll parameters, etc.).
  - [ ] Buttons for common actions (zero pose, snap FK to IK, etc.).

### 6. Error Checking and Reporting
- **Validation:**
  - [ ] Check for missing bones or naming conventions (warn if not standard).
  - [ ] Warn if FBX armature isn’t compatible (missing limbs, etc.).
