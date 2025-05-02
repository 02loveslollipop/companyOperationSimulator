import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import scipy.optimize as opt

class SkewedRandomGenerator:
    """
    A class that generates random values following a skewed normal distribution
    with specified minimum, maximum, and mean values.
    """
    
    def __init__(self, min_val, max_val, target_mean, skewness=0, batch_size=1000):
        """
        Initialize the random generator with the specified parameters.
        
        Parameters:
        -----------
        min_val : float
            Minimum value of the distribution
        max_val : float
            Maximum value of the distribution
        target_mean : float
            Target mean value of the distribution
        skewness : float, optional
            Skewness parameter (0 for normal distribution, negative for left skew, positive for right skew)
        batch_size : int, optional
            Number of samples to pre-generate in batches for efficiency
        """
        self.min_val = min_val
        self.max_val = max_val
        self.target_mean = target_mean
        self.skewness = skewness
        self.batch_size = batch_size
        
        # Optimize the distribution parameters
        self._optimize_parameters()
        
        # Pre-generate a batch of random values
        self._generate_batch()
    
    def _optimize_parameters(self):
        """Optimize the distribution parameters to match the target mean."""
        def find_distribution_params(params):
            loc, scale, a = params
            # Generate a sample from the distribution
            sample = stats.skewnorm.rvs(a, loc=loc, scale=scale, size=1000)
            # Clip to min and max values
            sample = np.clip(sample, self.min_val, self.max_val)
            # Calculate the mean
            mean_val = np.mean(sample)
            # Return the difference between the calculated mean and target mean
            return abs(mean_val - self.target_mean)
        
        # Initial guess for parameters: loc (location), scale, a (skewness parameter)
        initial_guess = [(self.min_val + self.max_val) / 2, 
                         (self.max_val - self.min_val) / 6, 
                         self.skewness]
        
        # Optimize to find parameters that give the desired mean
        result = opt.minimize(find_distribution_params, initial_guess, method='Nelder-Mead')
        
        # Get the optimized parameters
        self.loc, self.scale, self.a = result.x
        
        # Store the parameters as a dict too for convenience
        self.params = {
            "loc": self.loc,
            "scale": self.scale,
            "a": self.a
        }
    
    def _generate_batch(self):
        """Generate a new batch of random values following the distribution."""
        # Generate the distribution with optimized parameters
        distribution = stats.skewnorm.rvs(self.a, loc=self.loc, scale=self.scale, size=self.batch_size)
        
        # Clip values to stay within min_val and max_val
        distribution = np.clip(distribution, self.min_val, self.max_val)
        
        # Adjust to exactly match the target mean
        current_mean = np.mean(distribution)
        distribution = distribution + (self.target_mean - current_mean)
        
        # Final clip in case the adjustment pushed values outside the boundaries
        self.values = np.clip(distribution, self.min_val, self.max_val)
        
        # Initialize the index counter
        self.index = 0
    
    def random(self):
        """
        Return a random value following the specified distribution.
        
        Returns:
        --------
        float
            A random value from the specified distribution
        """
        # If we've used all pre-generated values, generate a new batch
        if self.index >= len(self.values):
            self._generate_batch()
        
        # Get the next value and increment the index
        value = self.values[self.index]
        self.index += 1
        
        return value
    
    def get_distribution_params(self):
        """
        Return the optimized distribution parameters.
        
        Returns:
        --------
        dict
            A dictionary containing the optimized parameters (loc, scale, a)
        """
        return self.params