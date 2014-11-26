#
# Originally this code from 'http://3dengine.org/Quaternions'
#


import math

class Quat:
    """
        Quaternion Class
        >>> roll = 30
        >>> pitch = 45
        >>> heading = 30
        >>> Q1 = Quat(0,0,1, roll) * Quat(1,0,0, pitch) * \
               Quat(0,1,0, heading)
        >>> Q1.gl_matrix()
        [0.57322332027622536, 0.73919890801437749, \
        -0.3535533898605015, 0.0, -0.3535533898605015, \
        0.61237244705783134, 0.70710677171312086, 0.0, \
        0.73919890801437749, -0.28033009198934633, \
        0.61237244705783134, 0.0, 0, 0, 0, 1.0]
    """
    def __init__(self, *args, **kwargs):
        if 'w' in kwargs:
            self.w = kwargs['w']
            self.x = kwargs['x']
            self.y = kwargs['y']
            self.z = kwargs['z']
        elif len(args)==4:
            #angle = (float(args[3]) / 180.) * 3.1415926
            angle = float(args[3]) 
            result = math.sin(angle / 2.)
            self.w = math.cos(angle / 2.)
            self.x = float(args[0]) * result
            self.y = float(args[1]) * result
            self.z = float(args[2]) * result
        else:
            self.w = 1.
            self.x = 0.
            self.y = 0.
            self.z = 0.

    def gl_matrix(self):
        """
           Returns OpenGL compatible modelview matrix
        """
        m = [0.] * 16
        m[0] = 1.0 - 2.0 * ( self.y * self.y + self.z * self.z )
        m[1] = 2.0 * (self.x * self.y + self.z * self.w)
        m[2] = 2.0 * (self.x * self.z - self.y * self.w)
        m[3] = 0.0 
        m[ 4] = 2.0 * ( self.x * self.y - self.z * self.w ) 
        m[ 5] = 1.0 - 2.0 * ( self.x * self.x + self.z * self.z )
        m[ 6] = 2.0 * (self.z * self.y + self.x * self.w ) 
        m[ 7] = 0.0 
        m[ 8] = 2.0 * ( self.x * self.z + self.y * self.w )
        m[ 9] = 2.0 * ( self.y * self.z - self.x * self.w )
        m[10] = 1.0 - 2.0 * ( self.x * self.x + self.y * self.y ) 
        m[11] = 0.0 
        m[12] = 0 
        m[13] = 0 
        m[14] = 0 
        m[15] = 1.0
        return m
    
    def __mul__(self, b):
        r = Quat()
        r.w = self.w*b.w - self.x*b.x - self.y*b.y - self.z*b.z
        r.x = self.w*b.x + self.x*b.w + self.y*b.z - self.z*b.y
        r.y = self.w*b.y + self.y*b.w + self.z*b.x - self.x*b.z
        r.z = self.w*b.z + self.z*b.w + self.x*b.y - self.y*b.x
        return(r)

