# Poser Autorigger for Blender

An autorigger for Poser characters imported as FBX files.

This auto-rigging tool is geared specifically towards FBX imported figures that already have an existing base armature. This tool takes that existing armature and automates the setup of IK/FK chains, bone collections, and bone widgets.

## **Workflow Summary**

1. User imports their FBX Poser character to Blender.
2. Runs auto-rigger script/addon.
3. Addon detects the armature, generates required IK/FK chains, creates controls, and assigns custom shapes.
4. Rig is ready for animation with standard Blender controls.


## Base Feature Set for Poser FBX Auto-Rigger in Blender

### 1. IK/FK Chain Creation
- **Limbs (Arms & Legs):**
  - Detect existing limb bones (shoulder, upper arm, forearm, hand, thigh, shin, foot).
  - Generate IK chains for arms and legs.
  - Generate FK chains for arms and legs.
  - Setup seamless IK/FK switching (custom properties, drivers, constraints).
- **Fingers:**
  - Detect finger bones.
  - Create FK controls for each finger.
  - Optionally, add simple IK for index fingers (for pointing, if needed).
- **Spine:**
  - Detect spine bones.
  - Create FK controls along the spine.
  - Optionally, create a simple IK spline for the spine for posing.

### 2. Foot Roll Control
- **Foot Rig Features:**
  - Add foot roll controller (using a custom bone or empty).
  - Setup constraints for toe bend, heel lift, ball roll, etc.
  - Automatic foot banking (side-to-side roll).
  - Lock/unlock foot/heel as needed.

### 3. Constraints Setup
- **Rig Constraints:**
  - Add necessary constraints for all IK and FK chains (IK, Copy Rotation, Limit Rotation, etc.).
  - Ensure pole targets are generated and positioned correctly for knees/elbows.
  - Setup drivers or custom properties for easy switching and control.

### 4. Control Custom-Shapes
- **Custom Bone Shapes:**
  - Assign custom shapes to each main control (IK handles, FK controls, foot roll, pole targets).
  - Use Blender’s built-in shapes or allow loading from a user-supplied blend file.

### 5. User Interface (Optional, but recommended for usability)
- **Rig UI Panel:**
  - Add a custom sidebar panel in Blender for rig controls (IK/FK switch, foot roll parameters, etc.).
  - Buttons for common actions (zero pose, snap FK to IK, etc.).

### 6. Error Checking and Reporting
- **Validation:**
  - Check for missing bones or naming conventions (warn if not standard).
  - Warn if FBX armature isn’t compatible (missing limbs, etc.).
