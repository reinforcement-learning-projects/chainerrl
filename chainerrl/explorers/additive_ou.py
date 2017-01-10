from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from logging import getLogger

from chainer import cuda
import numpy as np

from chainerrl import explorer


class AdditiveOU(explorer.Explorer):
    """Additive Ornstein-Uhlenbeck process.

    Used in https://arxiv.org/abs/1509.02971 for exploration.

    Args:
        mu (float): Mean of the OU process
        theta (float): Friction to pull towards the mean
        sigma (float): Scale of noise
    """

    def __init__(self, mu=0.0, theta=0.15, sigma=0.3,
                 logger=getLogger(__name__)):
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.logger = logger
        self.ou_state = None

    def evolve(self):
        # dx = theta (mu - x) + sigma dW
        # for a Wiener process W
        noise = np.random.normal(size=self.ou_state.shape, loc=0,
                                 scale=self.sigma)
        self.ou_state += self.theta * (self.mu - self.ou_state) + noise

    def select_action(self, t, greedy_action_func):
        a = greedy_action_func()
        if self.ou_state is None:
            sigma_stable = self.sigma / np.sqrt(2*self.theta - self.theta**2)
            self.ou_state = np.random.normal(size=a.shape,
                loc=self.mu, scale=sigma_stable).astype(np.float32)
        else:
            self.evolve()
        noise = self.ou_state
        self.logger.debug('t:%s noise:%s', t, noise)
        if isinstance(a, cuda.cupy.ndarray):
            noise = cuda.to_gpu(noise)
        return a + noise

    def __repr__(self):
        return 'AdditiveOU(mu={}, theta={}, sigma={})'.format(
            self.mu, self.theta, self.sigma)
