def quaternion_inverse(w, x, y, z):
    """
    Returns the inverse of a (possibly non-unit) quaternion.
    Inverse(q) = Conjugate(q) / ||q||^2
    """
    norm_sq = w*w + x*x + y*y + z*z
    return (w / norm_sq, -x / norm_sq, -y / norm_sq, -z / norm_sq)

def quaternion_multiply(w1, x1, y1, z1, w2, x2, y2, z2):
    """
    Returns the product of two quaternions q1 * q2.
    
    q1 = w1 + x1*i + y1*j + z1*k
    q2 = w2 + x2*i + y2*j + z2*k
    
    Product = (w1w2 - x1x2 - y1y2 - z1z2)
              + (w1x2 + x1w2 + y1z2 - z1y2) i
              + (w1y2 + y1w2 + z1x2 - x1z2) j
              + (w1z2 + z1w2 + x1y2 - y1x2) k
    """
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return (w, x, y, z)

def quaternion_relative(w0, x0, y0, z0, w1, x1, y1, z1):
    
    """
    Computes q_relative = q0^-1 * q1 where:
      q0 = (w0, x0, y0, z0) is the 'reference' quaternion
      q1 = (w1, x1, y1, z1) is the 'current' quaternion
    
    The returned quaternion represents the rotation needed to go
    from q0 to q1 (i.e., "delta" or "difference" quaternion).
    """
    
    if not all((w1, x1, y1, z1)):
        return (None, None, None, None) #gets caught & handled in outer scope
    
    # Step 1: invert q0
    inv_w0, inv_x0, inv_y0, inv_z0 = quaternion_inverse(w0, x0, y0, z0)
    
    # Step 2: multiply (q0^-1) by q1
    return quaternion_multiply(inv_w0, inv_x0, inv_y0, inv_z0, w1, x1, y1, z1)

# Example usage:
# Suppose q0 = (1, 0, 0, 0) (the identity quaternion, no rotation)
# and q1 = (0.707, 0.707, 0.0, 0.0) (a 90-degree rotation around X-axis).
# We expect the relative quaternion to simply be q1 again, because identity^-1 = identity.

# ref = (1.0, 0.0, 0.0, 0.0)    # q0
# current = (0.707, 0.707, 0.0, 0.0)  # q1 (approx rotation by 90° about X)

# rel = quaternion_relative(*ref, *current)
