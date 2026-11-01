"""Exact frozen Model.__init__/fields prefix; no optimizer/initialization."""
import numpy as np

class Model:
    def __init__(self, config):
        self.config = config
        mr, mc = config["ms1"]
        nr, nc = config["ms2"]
        self.M, self.N = mr*mc, nr*nc
        if nr == 0 or nc == 0:
            self.indices = np.empty((1, 0), dtype=int)
        else:
            if nr>mr or nc>mc:
                raise ValueError("MS2 must fit inside MS1")
            self.indices = np.array([[ (r+i)*mc+c+j for i in range(nr) for j in range(nc)]
                                     for r in range(mr-nr+1) for c in range(mc-nc+1)])
        self.U = len(self.indices)
        coords = np.array([[r, c] for r in range(mr) for c in range(mc)])
        az = np.deg2rad(config["azimuth_deg"])
        el = np.deg2rad(config["elevation_deg"])
        direction = np.column_stack((np.sin(el)*np.cos(az), np.sin(el)*np.sin(az)))
        self.c = np.exp(2j*np.pi*config["spacing_over_wavelength"]*(direction@coords.T))
        incidence = config["incidence_direction_cosines"]
        self.c *= np.exp(2j*np.pi*config["spacing_over_wavelength"]*(coords@incidence))[None,:]
        self.K = len(az)
        self.beta = np.broadcast_to(config.get("echo_beta_squared", 1), (len(az),)).copy()
        self.targets = config.get("number_of_targets", self.K)

    def fields(self, z):
        bar = np.ones((self.U, self.M), dtype=complex)
        for u, ix in enumerate(self.indices):
            bar[u, ix] = z["theta"]
        v = bar*z["phi"][None,:]
        q = self.c@v.T
        a = np.abs(q)**2
        return bar, v, q, a

