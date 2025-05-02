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
        
        # Calculate initial parameters
        self._calculate_parameters()
        
        # Pre-generate a batch of random values
        self._generate_batch()
    
    def _calculate_parameters(self):
        """Directly calculate distribution parameters based on the target range and mean."""
        self.logger.debug("Calculating distribution parameters")

        # Calculate range and relative position of mean
        range_size = self.max_val - self.min_val
        relative_mean = (self.target_mean - self.min_val) / range_size

        # Direct parameter calculation without optimization
        self.scale = range_size / 4  # Use 1/4 of range as scale for better spread
        
        # Calculate location based on target mean and skewness
        if abs(self.skewness) < 0.1:  # Almost symmetric
            self.loc = self.target_mean
            self.a = 0.1  # Minimal skewness
        else:
            # Adjust location based on skewness direction and magnitude
            skew_direction = 1 if self.skewness > 0 else -1
            skew_magnitude = min(abs(self.skewness), 3)  # Cap skewness at ±3
            
            # Adjust location proportionally to skewness
            self.loc = self.target_mean - (skew_direction * self.scale * skew_magnitude * 0.1)
            self.a = skew_magnitude * skew_direction

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
        
        # Generate base distribution
        distribution = stats.skewnorm.rvs(self.a, loc=self.loc, scale=self.scale, size=self.batch_size)
        
        # Apply quick bounds
        distribution = np.clip(distribution, self.min_val, self.max_val)
        
        # Fine-tune mean with minimal adjustments
        current_mean = np.mean(distribution)
        if abs(current_mean - self.target_mean) > 0.01 * self.scale:
            adjustment = self.target_mean - current_mean
            distribution += adjustment
            distribution = np.clip(distribution, self.min_val, self.max_val)
        
        # Store the batch
        self.values = distribution
        
        # Calculate and log statistics
        batch_mean = np.mean(self.values)
        batch_min = np.min(self.values)
        batch_max = np.max(self.values)
        self.logger.debug(f"Generated batch statistics - mean: {batch_mean:.2f}, min: {batch_min:.2f}, max: {batch_max:.2f}")
        
        # Reset index
        self.index = 0
    
    def random(self):
        """Return a random value following the specified distribution."""
        # Generate new batch if needed
        if self.index >= len(self.values):
            self._generate_batch()
        
        # Get and return next value
        value = float(self.values[self.index])
        self.index += 1
        
        self.logger.debug(f"Generated random value: {value}")
        return value
    
    def get_distribution_params(self):
        """Return the calculated distribution parameters."""
        return self.params.copy()