"""
Data generator simulating the evolution of a FOREX pair.

Of course FOREX processes do not necessarily strictly adher to the criterion of
stationarity (consider, e.g., the Brexit referendum vote, Trump/Biden election,
etcetc.), yet the approach considered here using the CKLS stochastic differential
equation is a close enough approximation, and anything more involved like jump processes
should be considered slighlty OTT.

Especially the addition of larger tails (through the skew) student t-distribution make
CKLS an acceptable modelling approach.
As not every situation is well-defined by a single distribution, there is the option of
using an interpolation of a discrete distribution for the data generation.
"""
import os
from typing import Union, Tuple, Dict

from scipy.special import beta as B
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import numpy as np
import pandas as pd
import joblib


class FOREXGenerator:
    """
    Forex data generator loosely based on a the CKLS (Chan–Karolyi–Longstaff–Sanders)
    variation of the Ornstein Uhlenbeck SDE.

    CKLS equation:
    dX_(n+1) = theta(mu - X(n))*dt +sigma*X(n)**d *dZ(n),
    where Z is, i.a., the skewed student t-distribution of returns, where
        return(t) = X(t) = price(t)-price(t-1).
    Although this class offers the ability to accept any reasonable sized [1000,5000]
    discrete distribution. To interpolate such a discrete distribution calculate with
    `self.interpolate_discrete_distribution()` using your discrete returns data.

    n ∈ [0,dT,...,N*dT], where N*dt = T
    Thus time granularity can be controlled and is of paramount importance for control
    of the mean reversion term.

    Either provide your own set of exchange rates, or work with the values preset for
    the example sub second tick set covering large parts of late 2020 and early 2021.
    """

    def __init__(
        self,
        x: float,
        currency_pair: str = "GBPAUD",
        dt: float = 0.05,
        discrete: bool = True,
    ) -> None:
        """
        Args:
            x (float): Value the currency pair will initiate at
            currency_pair (str): currency pair name
            dt (float): approximate seconds between consecutive data points
            discrete (bool): frequencies of returns distribution provided (true) or not (false)
        """

        self.x = x
        self.theta = 0.006 # Mean reversion speed (control the size and duration of spikes)
        self.mu = self.x # Long-term mean (the further from the initial `x`, the more initial movement)
        self.d = 0.5
        self.sigma = 0.094  # Drift term scale factor
        self.p = 1.5  # p and q determine skew student t (SGT) tail size
        self.q = 10  # p and q determine skew student t (SGT) tail size
        self.lambdas = -0.0082 # Skewness lambda
        self.mu_sgt = 0.001
        self.s = 0.0062  # SGT scale param s>0
        self.dT = dt  # Length of numeric approximation step
        self.timer = 0  # Timer for introducting gaps into data
        self.currencypair = currency_pair # Currency pair name
        self.vals = np.linspace(-1, 1, 50000) # Values in returns distribution (Z variable in above formula)

         # Frequency of values in returns distribution (Z variable in CKLS equation)
        if not discrete:
            # If frequencies not provided, then compute
            self.freq = self.skewed_generalized_student_t(self.vals) / sum(
                self.skewed_generalized_student_t(self.vals)
            )
        else:
            # Else, load the frequencies
            self.freq = self.load_discrete_interpolation(
                x_range=self.vals, currencypair=self.currencypair
            )
            self.freq /= self.freq.sum()
        
        # Load tick timing distributions
        self.tick_val = np.load("./generator_weights/val.npy")
        self.tick_freq = np.load("./generator_weights/freq.npy")
        
        # Generate larger range of RSI values for GBPAUD currency pair for the example use case
        if self.currencypair == 'GBPAUD':
            self.extreme_rsi = True
            # Constants to configure the larger range of RSI values
            self.rsi_up_min_factor = 0.05
            self.rsi_up_max_factor = 0.35
            self.rsi_down_min_factor = 0.05
            self.rsi_down_max_factor = 0.35
            self.movements = []
            self.direction = np.random.choice(['normal', 'up', 'down'])
            self.normal_timer = 2100
            self.up_down_timer = np.random.randint(2100, 4200)
        else:
            self.extreme_rsi = False
        
        pass

    def tick_timing_distrib(self) -> float:
        """Rough approximation of the tick distribution, which consists of ~2 piecewise
        monomials."""
        if self.currencypair == "CADJPY":
            # Produce long inter-tick gaps for this currency pair
            val = self.tick_val * 10
        else:
            val = self.tick_val
        freq = self.tick_freq
        freq = freq / freq.sum()
        return np.random.choice(val, p=freq, size=1)[0]

    def next(self) -> float:
        """Create next data point by plugging values into CKLS SDE."""
        # Introduce gaps into the data
        if (self.timer - self.dT) > 0:
            self.timer = self.timer - self.dT
            return None
        else:
            self.timer = self.tick_timing_distrib()
            
            if self.extreme_rsi:
                # Compute larger range of RSI values by enforcing larger increases (decreases) for an extended period

                # Switch to larger increases ('up'), larger decreases ('down'), or standard CKLS behaviour ('normal')
                # when threshold of number of data points reached
                positive_movements = self.movements.count(1)
                negative_movements = self.movements.count(-1)
                normal_movements = self.movements.count(0)
                if positive_movements > self.up_down_timer or negative_movements > self.up_down_timer:
                    self.direction = 'normal'
                    self.movements = []
                elif normal_movements > self.normal_timer:
                    self.direction = 'up' if np.random.random(1) <= 0.5 else 'down'
                    self.movements = []
                    self.up_down_timer = np.random.randint(2100, 4200)
                
                if self.direction == 'up':
                    # When enforcing larger increases, reduce magnitude of x_delta when it is negative
                    x_delta = (
                        self.theta * (self.mu - self.x) * self.dT
                        + self.sigma
                        * (self.x ** self.d)
                        * np.random.choice(self.vals, p=self.freq)
                    )

                    if x_delta < 0:
                        x_delta = x_delta * np.random.uniform(
                            low=self.rsi_up_min_factor, 
                            high=self.rsi_up_max_factor)

                    self.movements.append(1)
                    xn_1 = self.x + x_delta
                    self.x = xn_1

                elif self.direction == 'down':
                    # When enforcing larger decreases, reduce magnitude of x_delta when it is positive
                    x_delta = (
                        self.theta * (self.mu - self.x) * self.dT
                        + self.sigma
                        * (self.x ** self.d)
                        * np.random.choice(self.vals, p=self.freq)
                    )

                    if x_delta > 0:
                        x_delta = x_delta * np.random.uniform(
                            low=self.rsi_down_min_factor, 
                            high=self.rsi_down_max_factor)

                    self.movements.append(-1)
                    xn_1 = self.x + x_delta
                    self.x = xn_1

                else:
                    # Standard behaviour of CKLS equation
                    xn_1 = (
                        self.x
                        + self.theta * (self.mu - self.x) * self.dT
                        + self.sigma
                        * (self.x ** self.d)
                        * np.random.choice(self.vals, p=self.freq)
                    )

                    self.x = xn_1
                    self.movements.append(0)

            else:
                # Compute next value as per CKLS equation
                xn_1 = (
                    self.x
                    + self.theta * (self.mu - self.x) * self.dT
                    + self.sigma
                    * (self.x ** self.d)
                    * np.random.choice(self.vals, p=self.freq)
                )
                self.x = xn_1
        return xn_1

    def next_m(self, m: float) -> np.ndarray:
        """Create next 'm' data points by looping over `self.next()`"""
        x_n_1_to_n_m = np.zeros(shape=m)
        for _ in range(m):
            x_n_1_to_n_m[_] = self.next()
        return x_n_1_to_n_m

    def skewed_generalized_student_t(
        self,
        x: Union[float, np.ndarray],
        q: float = 1.5,
        p: float = 10,
        lambdas: float = -0.0082,
        s: float = 0.0062,
        mu: float = 0,
        from_class: bool = False,
    ) -> Union[float, np.ndarray]:
        """Sample from SGT distribution for 'return' x.
        For more info c.f. https://en.wikipedia.org/wiki/Skewed_generalized_t_distribution

        Args:
            x (float): Value at which the distribution will be sampled
            from_class (bool): copy parameter values from class values
            For other arguments' definitions, please see the class definition.
        Returns:
            float: next time step x(t+1)
        """
        # For the sake of readability of the formulae avoid self.*:
        if from_class:
            q = self.q
            p = self.p
            lambdas = self.lambdas
            s = self.s
            mu = self.mu_sgt
        v = q ** (-1 / p) * (
            (3 * lambdas ** 2 + 1) * (B(3 / p, q - 2 / p) / B(1 / p, q))
            - 4 * lambdas ** 2 * (B(2 / p, q - 1 / p) / B(1 / p, q)) ** 2
        ) ** (-1 / 2)
        m = 2 * v * s * lambdas * q ** (1 / p) * B(2 / p, q - 1 / p) / B(1 / p, q)

        f_x = p / (
            2
            * v
            * s
            * q ** (1 / p)
            * B(1 / p, q)
            * (
                np.abs(x - mu + m) ** p
                / (q * (v * s) ** p)
                * (lambdas * np.sign(x - mu + m) + 1) ** p
                + 1
            )
            ** (1 / p + q)
        )

        return f_x

    def fit_SGT(
        self,
        returns: Union[pd.Series, np.ndarray],
        freq: Union[int, bool] = False,
        update: bool = False,
    ) -> Dict:
        """
        Fit skewed generalised student t distribution to a Forex pair's returns.
        Returns being the difference between timesteps:
            returns(t=n) = price(t=n)-price(t=n-1),
        or simply with pandas: returns = pd.Series([...]).diff(1).fillna(0)

        Args:
            freq (int): number of histogram bins returns are divided into
            returns (Union[pd.Series, np.ndarray]): returns of a Forex pair
            update (bool): Update the parameters of the SGT for the class.

        Returns:
            dict: SGT parameters as obtained from fit.
        """
        param_list = ["q", "p", "lambdas", "s", "mu"]
        returns = returns.fillna(0)
        if freq:
            bin_amount = freq
        else:
            bin_amount = int(len(returns) / 7.5)
        returns_freq, returns_val = np.histogram(returns.values, bins=bin_amount)
        returns_val = returns_val[:-1]
        returns_freq = returns_freq / returns_freq.sum()
        param_guess = [self.q, self.p, self.lambdas, self.s, self.mu_sgt]
        
        param_bounds = (
            (0, 0, -1, 0, -np.inf),
            (np.inf, np.inf, 1, np.inf, np.inf),
        )
        optimised_params = curve_fit(
            self.skewed_generalized_student_t,
            xdata=returns_val,
            ydata=returns_freq,
            p0=param_guess,
            bounds=param_bounds,
        )[0]

        SGT_parameters = {
            param: optimised_params[i] for i, param in enumerate(param_list)
        }

        if update:
            self.q = optimised_params[0]
            self.p = optimised_params[1]
            self.lambdas = optimised_params[2]
            self.s = optimised_params[3]
            self.mu_sgt = optimised_params[4]
            self.vals = np.linspace(-0.3, 0.3, 10000)
            temp = self.skewed_generalized_student_t(
                self.vals,
                q=self.q,
                p=self.p,
                s=self.s,
                lambdas=self.lambdas,
                mu=self.mu_sgt,
            )
            self.freq = temp / sum(temp)

        return SGT_parameters, returns_freq, returns_val

    def interpolate_discrete_distribution(
        self,
        returns: Union[np.ndarray, pd.DataFrame],
        currencypair: str,
        update: bool = False,
        save: bool = False,
    ) -> Tuple:
        """Create an interpolation of a discrete returns distribution."""
        returns = pd.Series(returns)
        # Number of bins should be equal to, or less than the amount of unique data
        bins = returns.value_counts()
        returns_freq, returns_val = np.histogram(returns, bins=bins)
        returns_val = returns_val[:-1]
        # Amplify tails
        returns_freq[returns_freq == 1] = 2
        returns_freq[returns_freq == 0] = 1
        returns_freq = returns_freq / returns_freq.sum()
        interpolation = interp1d(returns_val, returns_freq)
        min_, max_ = returns_val.min(), returns_val.max()
        x_range = np.linspace(min_, max_, 10000)

        if update:
            self.vals = x_range
            self.freq = interpolation(x_range)
        if save:
            with open(
                os.path.abspath(f"./generator_weights/interpolator_{currencypair}.joblib"), "wb"
            ) as loc:
                joblib.dump(interpolation, loc)
        return x_range, interpolation(x_range)

    def load_discrete_interpolation(
        self, x_range: np.ndarray, currencypair: str = "GBPAUD"
    ) -> np.ndarray:
        """Load existing sub-second forex returns data interpolation and use for CKLS
        updates."""
        with open(
            os.path.abspath(f"./generator_weights/interpolator_{currencypair}.joblib"), "rb"
        ) as loc:
            interpolation = joblib.load(loc)
        return interpolation(x_range)