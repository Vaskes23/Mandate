# Phase 1: Quick Wins Implementation

## Status: In Progress

Based on CV.md analysis and Gemini's Independent Review & Validation.

---

## Step 1: Requirements Tracking File
- [x] Create requirements_phase1.md

---

## Step 2: Config Parameter Updates
- [ ] Update detection parameters (min_area, max_area, mog2_history, var_threshold, blur, morph)
- [ ] Update tracking parameters (max_disappeared, max_distance)
- [ ] Update spatial filter (horizon_line_percent)
- [ ] Update temporal filter (min_confirm_frames, min_move_distance)
- [ ] Update exclusion zones (wider lamp zone, disable debug drawing)
- [ ] Run tests
- [ ] Run linting
- [ ] User validation with npm run dev

---

## Step 3: CLAHE Contrast Enhancement
- [ ] Add CLAHE config options to config.json
- [ ] Add CLAHE instance variables to BirdDetector.__init__
- [ ] Modify preprocess_frame() to apply CLAHE before blur
- [ ] Add TestBirdDetectorCLAHE test class
- [ ] Run tests
- [ ] Run linting
- [ ] User validation with npm run dev

---

## Step 4: Frame Differencing Enhancement
- [ ] Add frame_diff config options to config.json
- [ ] Add frame_diff instance variables to BirdDetector.__init__
- [ ] Implement compute_frame_difference() method
- [ ] Modify detect() to combine MOG2 + frame diff masks
- [ ] Add TestBirdDetectorFrameDiff test class
- [ ] Run tests
- [ ] Run linting
- [ ] User validation with npm run dev

---

## Step 5: Persistence-Based Static Detection
- [ ] Add static_detection config section to config.json
- [ ] Add static detection instance variables to BirdDetector.__init__
- [ ] Implement _initialize_persistence_map() method
- [ ] Implement update_persistence_map() method
- [ ] Implement compute_static_mask() method
- [ ] Implement apply_static_mask() method
- [ ] Implement reset_static_detection() method
- [ ] Modify detect() to use static detection
- [ ] Add test fixtures to conftest.py
- [ ] Add TestBirdDetectorStaticDetection test class
- [ ] Run tests
- [ ] Run linting
- [ ] User validation with npm run dev

---

## Final Validation
- [ ] All pytest tests pass
- [ ] All linting passes
- [ ] FPS > 15 maintained
- [ ] Memory stable
- [ ] Detection quality improved (fewer false positives, small birds detected)
