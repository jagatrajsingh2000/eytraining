import numpy as np

# Create a 3x3 array of random floats using the recommended generator
rng = np.random.default_rng()
random_array = rng.random((3, 3))

print("3x3 Array of Random Floats:")
print(random_array)
