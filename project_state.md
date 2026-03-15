# Project State - MuJoCO Tendon Demo Core

Historical note: this file reflects an older project snapshot. The active script layout now uses `scripts/common/`, `scripts/data_tools/`, and `scripts/diagnostics/`.

## Current Status Summary

**Overall Status**: Complete training pipeline with behavior cloning operational and scripts organized

The project has a fully operational training pipeline with three-phase grasping demonstrations and behavior cloning:

1. ✅ **Three-phase grasping demo** (`demo_grasp.py`) with 500-step sequence
2. ✅ **Behavior cloning training** (`train_bc.py`) with simple MLP implementation
3. ✅ **Data visualization suite** (`visualize_data.py`) with four chart types
4. ✅ **Script organization** - 6 core scripts, 10 utility scripts in `archive/`
5. ✅ **Expert data collection** pipeline with controller-based demonstrations
6. ✅ **Complete training environment** (`ShadowGraspEnv`) with standard RL interface
7. ✅ **Data validation** tools for quality assurance
8. ✅ **Controller infrastructure** for coordinated grasping motions
9. ✅ **Catch task implementation** - True object catching (not just contact detection)

**Next Phase**: BC policy evaluation and larger dataset collection for robust training.

## ✅ Working Components

### 1. Core Infrastructure
- **Model loading**: All three model types load correctly (Shadow Hand, Arm26, Tendon)
- **Path utilities**: Fixed PROJECT_ROOT calculation (was off by one level)
- **Controller architecture**: BaseController and all three implementations functional
- **Script organization**: 6 core scripts in root, 10 utility scripts in `archive/`

### 2. Key Features Operational
- **Three-phase grasping demo**: Approach → close fingers → lift (500 steps)
- **Behavior cloning training**: Simple MLP (70→64→24) with PyTorch
- **Data visualization suite**: Four chart types (rewards, actions, observations, episodes)
- **Unified controller interface** with factory pattern
- **Multiple controller implementations** (linear, bio-inspired, enhanced)
- **Model information printing** and basic statistics
- **Command-line interface** for all scripts
- **Interactive grasp demonstration** (with optional keyboard control)

### 3. Training Environment System (Operational)
- **ShadowGraspEnv**: Complete RL environment with standard interface
  - `reset()`, `step(action)`, `get_obs()`, `compute_reward()`, `is_success()`
  - Action space: 24D (normalized to [-1, 1])
  - Observation space: 70D (31q + 30v + 9 positions)
  - Reward function: distance + contact + maintain + catch reward + ground penalty + action penalty
  - Success condition: continuous contact for 50 steps AND object not touching floor (true catching)
  - **Enhanced controller integration**: Three-phase grasping logic

### 4. Three-Phase Grasping Demo (New)
- **demo_grasp.py**: Complete grasping demonstration
  - Three-phase logic: approach (200 steps), close fingers (100 steps), lift (200 steps)
  - Total 500 steps for complete sequence
  - Viewer integration with automatic phase transitions
  - Configurable via command-line arguments
  - Success tracking and statistics

### 5. Behavior Cloning Training (New)
- **train_bc.py**: Minimal BC training implementation
  - Simple MLP architecture: 70 → 64 → 24 with Tanh output
  - PyTorch-based training with MSE loss and Adam optimizer
  - Model saving/loading to `.pth` files
  - Configurable epochs, batch size, learning rate

### 6. Data Visualization Suite (New)
- **visualize_data.py**: Comprehensive data visualization
  - Reward analysis chart (per-step and cumulative)
  - Action distribution histogram
  - Observation analysis (range and distribution)
  - Episode comparison (reward trajectories)
  - Automatic figure generation to `figures/` directory

### 7. Data Collection Pipeline (Operational)
- **Expert data collection**: `scripts/collect_expert_data.py`
  - Support for all controller types (linear, bio, enhanced)
  - Configurable episodes, steps, grasp strength
  - Automatic data normalization and validation
  - Output format: compressed NPZ with metadata
- **Data validation**: `scripts/check_dataset.py`
  - Quality checks (NaN, infinite values, range validation)
  - Statistical analysis (reward distribution, success rate)
  - Dimension consistency verification

### 8. Testing & Debugging Tools (in archive/)
- **Environment testing**: `scripts/archive/test_env.py` (with/without viewer)
- **Grasp testing**: `scripts/archive/test_grasp.py` and `test_grasp_direct.py`
- **Visualization debugging**: `scripts/archive/debug_viewer.py` and `test_viewer_simple.py`
- **Reward validation**: `scripts/archive/check_reward.py`
- **Environment validation**: `scripts/archive/validate_env.py`
- **Controller testing**: `scripts/archive/test_controllers.py`
- **Model inspection**: `scripts/archive/inspect_model.py`
- **Demo launcher**: `scripts/archive/run_demo.py`

### 9. Models Available
- **Shadow Hand E3M5**: Complete right hand model with assets
- **Arm26**: Simple arm model with tendon mechanics
- **Tendon**: Minimal tendon model for basic experiments

## ⚠️ Issues Requiring Attention

### 1. **Training Pipeline Issues**

**Action Range Violation**:
- Controller outputs exceed [-1, 1] range ([-0.955, 2.397] in test data)
- Cause: Denormalization may not perfectly constrain values
- Impact: Environment may clip actions, causing training mismatch
- **Priority**: Medium - Should be fixed for consistent behavior

**Dataset Size**:
- Current test dataset only 2 episodes (400 steps)
- Need 100+ episodes for robust BC training
- **Priority**: High - Collect larger dataset before serious BC training

**BC Policy Evaluation**:
- No evaluation script to test trained BC models
- Cannot measure success rate of learned policies
- **Priority**: Medium - Need to create `eval_bc.py` or similar

### 2. **Minor Issues**

**Path Utility Testing**:
- `src/utils/path_utils.py` standalone test fails due to relative import
- Not critical for main functionality, only affects direct module execution

**Model Loader Testing**:
- `src/utils/model_loader.py` cannot run standalone due to import structure
- Requires proper Python path setup

**Script Import Paths**:
- Archive scripts have fixed import paths (`../..` instead of `..`)
- Core scripts use relative imports correctly

### 3. **Dependency Issues**

**Optional Dependencies**:
- `pynput` needed for full keyboard interaction in interactive demos
- `matplotlib` needed for visualization in controller tests
- Both are optional but enhance functionality

**MuJoCo Viewer Compatibility**:
- Some users report hand not moving in viewer (may require spacebar to unpause)
- Viewer synchronization timing may need adjustment
- **Workaround**: Use `--no-viewer` flag for data collection

## 🔧 Recent Changes & Fixes

### Fixed (2026-03-09):
1. **Path Utility Root Calculation** (`src/utils/path_utils.py`):
   - Changed: `PROJECT_ROOT = Path(__file__).parent.parent.absolute()`
   - To: `PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()`
   - Reason: utils directory is `src/utils/`, so need to go up three levels to project root

2. **Model Inspection Script** (`scripts/inspect_model.py`):
   - Fixed numpy array indexing for `jnt_range` and `actuator_ctrlrange` (2D array access)
   - Fixed `actuator_type` attribute name (changed to `actuator_dyntype`)
   - Fixed `actuator_trnid` indexing (2D array access)
   - Added proper type conversions for MuJoCo array elements
   - **Status**: Fully functional for all three model types

### Added (2026-03-09):
1. **New Utility Script**: `scripts/inspect_model.py`
   - Purpose: Detailed model structure inspection
   - Features: Joint/actuator/tendon information, action/state space guidance
   - Status: **Fully functional** - tested with Shadow Hand, Arm26, and Tendon models
   - Output: Clear console formatting and JSON output option

### Fixed & Added (2026-03-10 to 2026-03-11):
1. **Three-Phase Grasping Demo**: `scripts/demo_grasp.py`
   - Complete 500-step grasping sequence: approach(200), close(100), lift(200)
   - Enhanced controller with automatic phase transitions
   - Viewer integration with extended duration
   - Fixed premature ending at 250 steps

2. **Behavior Cloning Training**: `scripts/train_bc.py`
   - Simple MLP architecture: 70 → 64 → 24 with Tanh output
   - PyTorch implementation with MSE loss and Adam optimizer
   - Model saving/loading to `.pth` files
   - Configurable training parameters

3. **Data Visualization Suite**: `scripts/visualize_data.py`
   - Four visualization types: rewards, actions, observations, episodes
   - Automatic figure generation to `figures/` directory
   - Statistical analysis and quality assessment

4. **Script Organization**:
   - Created `scripts/archive/` directory for non-core scripts
   - Moved 10 utility scripts to archive: `run_demo.py`, `test_controllers.py`, etc.
   - Kept 6 core scripts in root: `demo_grasp.py`, `collect_expert_data.py`, `check_dataset.py`, `visualize_data.py`, `train_bc.py`, `README.md`
   - Fixed import paths in archive scripts (`../..` instead of `..`)

5. **Complete Training Environment**: `src/environments/shadow_grasp_env.py`
   - Standard RL interface: `reset()`, `step()`, `get_obs()`, `compute_reward()`, `is_success()`
   - Robust body detection with multiple search patterns
   - Action normalization/denormalization for controller compatibility
   - Success condition: continuous contact for 50 steps

6. **Expert Data Collection Pipeline**:
   - `scripts/collect_expert_data.py`: Controller-based demonstration collection
   - `scripts/check_dataset.py`: Data quality validation and statistics
   - Support for all controller types with configurable parameters
   - NPZ format with metadata for BC training

7. **Critical Bug Fixes**:
   - Object detection: Multiple search patterns for robust body finding
   - Floor detection: Handle floor as geom (not body) in scene_right.xml
   - Contact detection: Proper handling of None floor_body_id
   - Added `_denormalize_action()` method for controller compatibility
   - Unicode encoding issues in demo scripts (replaced emojis with text)

### Added (2026-03-12): Catch Task Implementation
1. **True object catching task** (not just contact detection):
   - New success condition: hand-object contact AND object NOT touching floor
   - Object initial falling velocity (-0.3 m/s) to simulate "ball falling" scenario
   - Enhanced controller timing optimization (80-30-50 steps for faster response)
   - New reward components: catch reward (+15.0) and ground contact penalty (-20.0)
   - Backward compatible: `enable_catch_task=False` defaults to old behavior

2. **New validation script**: `scripts/test_catch_task.py`
   - Tests ball falling physics and catching feasibility
   - Records object height and ground contact statistics
   - Measures catching success rate with optimized controller

3. **Environment enhancements**:
   - Added `_check_object_on_floor()` method for ground contact detection
   - Added `_find_object_joint()` for velocity setting
   - Extended `info` dictionary with catch-related metrics
   - Updated `demo_grasp.py` and `collect_expert_data.py` with catch task support

## 📊 Model Specifications (Verified)

### Shadow Hand (scene_right.xml):
```
nq = 31      # Joint positions
nv = 30      # Joint velocities
nu = 24      # Actuators
nbody = 27   # Bodies
njnt = 25    # Joints
ntendon = 0  # Tendons (Shadow Hand uses direct joint control)
ngeom = 64   # Geometric objects
nsensor = 0  # Sensors
nmocap = 0   # Motion capture bodies
```

### Actuator Configuration:
- 24 actuators total
- Finger grouping: wrist(2), thumb(5), index(4), middle(4), ring(4), little(5)
- Control ranges: Most have limited ranges (check with inspect_model.py)

## 🧪 Testing Status

### Verified Working (Core Scripts):
- [x] Three-phase grasping demo (`demo_grasp.py`)
- [x] Behavior cloning training (`train_bc.py`)
- [x] Data visualization suite (`visualize_data.py`)
- [x] Expert data collection pipeline (`collect_expert_data.py`)
- [x] Data validation and quality checking (`check_dataset.py`)
- [x] Training environment creation and validation (`ShadowGraspEnv`)
- [x] Model loading (all three types)
- [x] Basic controller instantiation
- [x] Catch task validation script (`test_catch_task.py`)

### Verified Working (Archive Scripts):
- [x] Environment testing with viewer integration (`archive/test_env.py`)
- [x] Grasp testing utilities (`archive/test_grasp.py`, `test_grasp_direct.py`)
- [x] Viewer debugging tools (`archive/debug_viewer.py`, `test_viewer_simple.py`)
- [x] Controller testing framework (`archive/test_controllers.py`)
- [x] Demo script execution (`archive/run_demo.py`)
- [x] Model inspection (`archive/inspect_model.py`)
- [x] Environment validation (`archive/validate_env.py`, `check_reward.py`)

### Needs Verification:
- [ ] Action range constraint enforcement (exceeds [-1, 1])
- [ ] BC policy evaluation (need evaluation script)
- [ ] Larger dataset collection (100+ episodes)
- [ ] BC model generalization performance

### Untested:
- [ ] Full interactive grasp demo with keyboard (requires pynput)
- [ ] Controller comparison visualization (requires matplotlib)
- [ ] Advanced enhanced controller features (force feedback modes)
- [ ] Cross-platform viewer compatibility

## 📝 TODO List

### High Priority (BC Training Completion):
1. **BC policy evaluation script** - Create `eval_bc.py` to test trained models
2. **Large-scale data collection** - Collect 100+ episodes for robust BC training
3. **Action range enforcement** - Ensure controller outputs stay within [-1, 1] bounds
4. **Dataset quality improvement** - Tune controller for consistent high-success demonstrations

### Medium Priority (Pipeline Enhancement):
1. **Data augmentation** - Add noise/perturbation to improve BC robustness
2. **Expert policy evaluation** - Quantify controller performance metrics
3. **Training visualization** - Monitor BC training progress and metrics
4. **Hyperparameter tuning** - Optimize BC model architecture and training parameters

### Low Priority (Infrastructure):
1. **Interactive demonstration tools** - Keyboard control for manual data collection
2. **Advanced controller features** - Test force feedback and adaptive control modes
3. **Unit testing framework** - Add comprehensive tests for critical components
4. **Documentation** - Update API docs and add training tutorials

## 🚀 Recommended Next Steps

### Immediate (1-2 hours): BC Evaluation Setup
1. **Create BC evaluation script** (`eval_bc.py`):
   - Load trained BC model
   - Run policy in environment
   - Measure success rate and rewards
   - Compare with expert controller

2. **Collect larger dataset** (10-20 episodes):
   ```bash
   python scripts/collect_expert_data.py --episodes 20 --output data/bc_dataset_20.npz
   ```

3. **Train and evaluate BC model**:
   ```bash
   # Train on larger dataset
   python scripts/train_bc.py --data data/bc_dataset_20.npz --epochs 50 --output models/bc_20ep.pth

   # Evaluate (once eval_bc.py exists)
   python scripts/eval_bc.py --model models/bc_20ep.pth --episodes 10
   ```

### Short-term (1-2 days): Pipeline Improvement
1. **Fix action range enforcement**:
   - Add clamping in `_denormalize_action()` method
   - Ensure all actions stay within [-1, 1]

2. **Improve data visualization**:
   - Add training curve plots to `visualize_data.py`
   - Create BC policy comparison visualizations

3. **Enhance three-phase demo**:
   - Add success/failure statistics
   - Include object position tracking plots

### Medium-term (3-5 days): Advanced BC
1. **Implement DAgger** (Dataset Aggregation):
   - Iterative BC training with expert corrections
   - Automatic data collection during evaluation

2. **Hyperparameter optimization**:
   - Grid search for BC model architecture
   - Learning rate scheduling
   - Regularization techniques

### Medium-term (1 week): Pipeline Enhancement
1. **Improve expert demonstrations**:
   - Implement heuristic exploration for better state coverage
   - Add data augmentation (noise, perturbations)
   - Create mixed-quality datasets for robust learning
2. **Advanced BC techniques**:
   - Implement DAgger (Dataset Aggregation) for iterative improvement
   - Add regularization techniques (dropout, weight decay)
   - Experiment with different network architectures
3. **Performance benchmarking**:
   - Establish baseline metrics for different controllers
   - Compare BC vs random policy vs expert
   - Analyze failure modes and improvement areas

## 🔍 Technical Debt

### Code Quality:
- **Good**: Modular architecture, clear separation of concerns
- **Needs improvement**: Error handling in some edge cases
- **Technical debt**: Some duplicate code could be further refactored

### Documentation:
- **Good**: Comprehensive README.md and CLAUDE_CONTEXT.md
- **Adequate**: Code comments and docstrings
- **Could be better**: API documentation for controller development

### Testing:
- **Minimal**: Functional but not comprehensive
- **Need**: Unit tests for utility modules
- **Need**: Integration tests for demos

## 🏗️ Architecture Assessment

### Strengths:
1. **Clean separation**: Controllers, utilities, demos clearly separated
2. **Unified interfaces**: BaseController provides consistent API
3. **Factory pattern**: Easy controller creation and registration
4. **Extensible**: Easy to add new models, controllers, demos
5. **Minimal dependencies**: Core requires only mujoco and numpy

### Weaknesses:
1. **Error handling**: Some edge cases not fully handled
2. **Testing**: Lack of comprehensive test suite
3. **Documentation**: Could use more examples and tutorials

### Opportunities:
1. **RL integration**: Ready for reinforcement learning environments
2. **Multi-hand support**: Architecture supports different hand models
3. **Web interface**: Could add web-based visualization

## 📈 Performance Considerations

### Runtime Performance:
- **Model loading**: Fast with MuJoCo's efficient XML parsing
- **Controller computation**: Minimal overhead for all three controllers
- **Viewer performance**: Depends on system graphics capabilities

### Memory Usage:
- **Model memory**: MuJoCo manages internal model representation
- **Control history**: Limited to 1000 entries by default
- **Asset loading**: 3D models loaded on demand

## 🔗 Dependencies & Compatibility

### Core Dependencies:
- **MuJoCo 3.0+**: Required, follow official installation instructions
- **NumPy 1.21+**: Standard numerical computing

### Python Version:
- **Tested with**: Python 3.8+ (assumed, based on syntax)
- **Compatibility**: Should work with Python 3.8-3.12

### Platform Support:
- **Linux/macOS**: Fully supported
- **Windows**: Should work but may require additional setup for MuJoCo

## 🎯 Success Criteria Met

### Phase 1 (Productized Demo Suite): ✅
- Unified demo launcher with command-line interface
- Configurable controller selection and parameters
- Multiple demonstration scenarios

### Phase 2 (Controller Unified Interface): ✅
- BaseController abstract class
- Three implemented controllers with unified API
- Controller factory and registry
- Performance comparison framework

### Phase 3 (Training Pipeline Foundation): ✅
- Complete RL environment (`ShadowGraspEnv`) with standard interface
- Expert data collection pipeline (`collect_expert_data.py`)
- Data validation tools (`check_dataset.py`)
- Comprehensive testing and debugging infrastructure
- Ready for behavior cloning implementation

### Phase 4 (Interface Isolation): ✅
- BaseController abstracts hand-specific details with unified API
- Model loader supports multiple model types (Shadow Hand, Arm26, Tendon)
- Path configuration extensible for new models and assets
- Action normalization isolates controller from environment specifics
- Factory pattern enables easy controller swapping and comparison

## 📅 Project Timeline

### Phase 1: Foundation (Completed):
- Project extraction and refactoring from original codebase
- Utility module consolidation and validation
- Controller interface unification with factory pattern
- Demo script standardization and testing

### Phase 2: Training Infrastructure (Completed):
- Complete RL environment implementation (`ShadowGraspEnv`)
- Expert data collection pipeline (`collect_expert_data.py`)
- Data validation and quality checking tools
- Comprehensive testing and debugging infrastructure
- Viewer integration and visualization support

### Phase 3: BC Implementation (Completed):
- Behavior cloning training script development (`train_bc.py`)
- Three-phase grasping demonstration (`demo_grasp.py`)
- Data visualization suite (`visualize_data.py`)
- Script organization (core + archive structure)

### Phase 4: BC Evaluation & Enhancement (Current):
- BC policy evaluation script development
- Larger dataset collection (100+ episodes)
- Action range enforcement and quality improvements
- Hyperparameter tuning for BC models
- Catch task implementation (true object catching, not just contact)

### Phase 5: Advanced Features (Planned):
- DAgger implementation for iterative improvement
- Multi-task learning (grasp, lift, manipulate)
- Advanced controller modes (force feedback, adaptive control)
- Performance optimization and benchmarking

---

*Last updated: 2026-03-12*
*For comprehensive project overview, see `CLAUDE_CONTEST.md`*
