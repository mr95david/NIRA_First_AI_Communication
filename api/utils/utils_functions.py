def getInitialPose(
    # Valores padrão: ponto de partida dos experimentos
    x:float = -0.00690361,
    y:float = 0.13486863,
    z_or:float = 0.0003687,
    w_or:float = 0.99999
) -> dict:
    """Monta a mensagem PoseWithCovarianceStamped (frame 'map') para /set_initial_pose."""
    pose_order = {
    'header': {
        'stamp': {
            'secs': 0,
            'nsecs': 0
        },
        'frame_id': 'map'
    },
    'pose': {
        'pose': {
            'position': {
                'x': x,
                'y': y,
                'z': 0.0
            },
            'orientation': {
                'x': 0.0,
                'y': 0.0,
                'z': z_or,
                'w': w_or
            }
        },
        'covariance': [0.0] * 36  # Covariância padrão
    }
}
    return pose_order