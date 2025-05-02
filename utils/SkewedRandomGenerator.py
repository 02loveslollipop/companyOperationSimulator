import numpy as np
import scipy.stats as stats
import logging

class SkewedRandomGenerator:
    """
    A class that generates random values following a skewed normal distribution
    with specified minimum, maximum, and mean values.
    """
    logger = logging.getLogger('SkewedRandomGenerator')
    
    def __init__(self, min_val, max_val, target_mean, skewness=0, batch_size=100):
        self.logger.debug(f"Initializing generator: min={min_val}, max={max_val}, mean={target_mean}, skewness={skewness}")
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.target_mean = float(target_mean)
        self.skewness = float(skewness)
        self.batch_size = batch_size
        
        # Validate inputs
        if self.min_val >= self.max_val:
            raise ValueError("min_val must be less than max_val")
        if self.target_mean < self.min_val or self.target_mean > self.max_val:
            raise ValueError("target_mean must be between min_val and max_val")
        
        # Directly calculate distribution parameters
        self._calculate_parameters()
        
        # Pre-generate a batch of random values
        self._generate_batch()
    
    def _calculate_parameters(self):
        """Directly calculate the distribution parameters based on min, max, and mean."""
        self.logger.debug("Calculating distribution parameters")

        # Calculate parameters based on the target range and mean
        range_size = self.max_val - self.min_val
        relative_mean = (self.target_mean - self.min_val) / range_size

        # Base scale on range size to ensure good coverage
        self.scale = range_size / 4  # Using 4 instead of 6 for wider spread

        # Calculate location parameter to achieve target mean
        # For symmetric distribution (skewness = 0), loc will be target_mean
        # For skewed distributions, adjust loc based on skewness direction and magnitude
        skew_factor = np.clip(self.skewness, -3, 3)  # Limit skewness range
        if relative_mean <= 0.5:
            # Left side of range - adjust loc rightward for negative skew
            self.loc = self.target_mean + (self.scale * skew_factor * 0.1)
            self.a = max(-skew_factor, 0.1)  # Ensure some minimum skewness
        else:
            # Right side of range - adjust loc leftward for positive skew
            self.loc = self.target_mean - (self.scale * skew_factor * 0.1)
            self.a = max(skew_factor, 0.1)  # Ensure some minimum skewness

        # Store parameters
        self.params = {
            "loc": self.loc,
            "scale": self.scale,
            "a": self.a
        }
        
        self.logger.debug(f"Calculated parameters: {self.params}")
    
    def _generate_batch(self):
        """Generate a new batch of random values following the distribution."""
        self.logger.debug("Generating new batch of random values")
        
        # Generate more values than needed to allow for filtering
        n_extra = int(self.batch_size * 1.5)
        distribution = stats.skewnorm.rvs(self.a, loc=self.loc, scale=self.scale, size=n_extra)
        
        # Clip values to stay within min_val and max_val
        distribution = np.clip(distribution, self.min_val, self.max_val)
        
        # Add some controlled randomness around the target mean
        mean_adjustment = np.random.normal(0, self.scale * 0.01, size=len(distribution))
        distribution = distribution + mean_adjustment
        
        # Reclip after adjustment
        distribution = np.clip(distribution, self.min_val, self.max_val)
        
        # Ensure we have exactly batch_size values
        if len(distribution) > self.batch_size:
            distribution = distribution[:self.batch_size]
        
        # Store the batch
        self.values = distribution
        
        # Calculate and log statistics
        batch_mean = np.mean(self.values)
        batch_min = np.min(self.values)
        batch_max = np.max(self.values)
        self.logger.debug(f"Generated batch statistics - mean: {batch_mean:.2f}, min: {batch_min:.2f}, max: {batch_max:.2f}")
        
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
        value = float(self.values[self.index])
        self.index += 1
        
        self.logger.debug(f"Generated random value: {value}")
        return value
    
    def get_distribution_params(self):
        """
        Return the calculated distribution parameters.
        
        Returns:
        --------
        dict
            A dictionary containing the parameters (loc, scale, a)
        """
        return self.params.copy()