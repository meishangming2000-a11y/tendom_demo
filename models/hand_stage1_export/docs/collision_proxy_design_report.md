# Collision Proxy Design Report

- Source hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_clean_mesh_export2_draft.xml`
- Output hand MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\hand_stage1_visual_clean_collision_proxy.xml`
- Output scene MJCF: `D:\tendon_project\simulations\models\hand_stage1_export\mjcf\scene_ball_visual_clean_collision_proxy.xml`
- Clean STL visual geoms remain visual-only: `contype=0`, `conaffinity=0`, `group=2`.
- Collision does not use STL mesh geoms.
- Collision proxy uses the existing primitive skeleton geoms, renamed and marked as `group=3`.
- Hand proxy collision mask is `contype=1`, `conaffinity=2`: it contacts the ball and ground, but not other hand proxy geoms.
- Debug markers remain non-colliding in `group=4`.

## Counts

- Clean visual geoms: 23
- Collision proxy geoms: 28
- Debug marker geoms: 48
- Compiled collision geoms: 30
- Fingertip sites retained: 5

## Proxy Source

- Palm, wrist/base, long-finger phalanx, distal, and thumb segment collision proxies are inherited from the current primitive skeleton.
- This is deliberate: uncertain clean CAD mesh shapes are not used as collision until body-local mesh/collision design is confirmed.
- TODO: tune palm and thumb proxy shapes after SolidWorks axes and link-local frames are confirmed.

## Proxy Geoms

- `hand_base_link_collision_proxy` type=box size=`0.026 0.020 0.014` pose=`0 0 -0.006`
- `wrist_middle_link_collision_proxy` type=capsule size=`0.011` pose=`0 -0.018 0 0 0.018 0`
- `palm_link_collision_proxy_ellipsoid` type=ellipsoid size=`0.030 0.064 0.024` pose=`0 0.048 0.002`
- `palm_link_index_mcp_flex_joint_collision_proxy_spoke` type=capsule size=`0.0055` pose=`0 0 0 -0.0014333 0.10034 -0.024803`
- `palm_link_middle_mcp_flex_joint_collision_proxy_spoke` type=capsule size=`0.0055` pose=`0 0 0 -0.0014333 0.097567 -0.0048026`
- `palm_link_ring_mcp_flex_joint_collision_proxy_spoke` type=capsule size=`0.0055` pose=`0 0 0 -0.0014333 0.090989 0.015197`
- `palm_link_little_mcp_flex_joint_collision_proxy_spoke` type=capsule size=`0.0055` pose=`0 0 0 -0.0014333 0.082348 0.035197`
- `palm_link_thumb_root_connector_fixed_joint_collision_proxy_spoke` type=capsule size=`0.0055` pose=`0 0 0 0.0064688 0.019332 -0.016418`
- `index_mcp_flex_link_collision_proxy` type=capsule size=`0.0058` pose=`0 0 0 -0.00051676 0.0097417 -0.00026674`
- `index_proximal_phalanx_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 -0.00021096 0.034999 0.00025`
- `index_proximal_inter_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.0097266 0.027252 -0.00045437`
- `index_distal_link_collision_proxy` type=capsule size=`0.0062` pose=`0 0 0 0.011092027 0.02570919 -6.7061438e-05`
- `middle_mcp_flex_link_collision_proxy` type=capsule size=`0.0058` pose=`0 0 0 -0.00064254 0.0097342 -0.00026674`
- `middle_proximal_phalanx_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.044915 -0.0027578 -0.0003`
- `middle_proximal_inter_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.03498 -0.0011685 -0.0002`
- `middle_distal_link_collision_proxy` type=capsule size=`0.0062` pose=`0 0 0 0.027301483 -0.006215095 -4.054405e-05`
- `ring_mcp_flex_link_collision_proxy` type=capsule size=`0.0058` pose=`0 0 0 -0.00087181 0.0097164 -0.00026674`
- `ring_proximal_phalanx_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.039933 -0.0023102 -0.0003`
- `ring_proximal_inter_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.0039743 0.029736 -0.0002`
- `ring_distal_link_collision_proxy` type=capsule size=`0.0062` pose=`0 0 0 0.02673319 -0.008326736 -4.4812211e-05`
- `little_mcp_flex_link_collision_proxy` type=capsule size=`0.0058` pose=`0 0 0 -0.0018088 0.0095862 -0.00026674`
- `little_proximal_phalanx_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.034983 -0.0010805 -0.0003`
- `little_proximal_inter_link_collision_proxy` type=capsule size=`0.0072` pose=`0 0 0 0.00077177 0.024988 -0.0002`
- `little_distal_link_collision_proxy` type=capsule size=`0.0062` pose=`0 0 0 0.026961144 -0.007556097 -4.6194307e-05`
- `thumb_root_connector_link_collision_proxy` type=capsule size=`0.0068` pose=`0 0 0 -6.3364e-05 0.00012377 -0.011586`
- `thumb_metacarpal_link_collision_proxy` type=capsule size=`0.0068` pose=`0 0 0 -0.016224 0.049404 -0.000175`
- `thumb_proximal_link_collision_proxy` type=capsule size=`0.0068` pose=`0 0 0 -0.0033345 0.031826 -0.000105`
- `thumb_distal_link_collision_proxy` type=capsule size=`0.0068` pose=`0 0 0 0.00052061935 -0.027995157 -1.2280723e-05`
