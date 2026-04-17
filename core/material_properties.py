# Material Properties Database

# This database contains material properties for various substances used in Fan Dampers.

class Material:
    def __init__(self, name, thermal_conductivity, density, specific_heat):
        self.name = name  # Name of the material
        self.thermal_conductivity = thermal_conductivity  # W/(m·K)
        self.density = density  # kg/m^3
        self.specific_heat = specific_heat  # J/(kg·K)

    def __repr__(self):
        return f"{self.name}(k={self.thermal_conductivity}, density={self.density}, c={self.specific_heat})"

# Temperature-dependent properties

def temperature_dependent_properties(material, temperature):
    if material.name == 'Steel':
        # Example coefficients for temperature-dependent properties of Steel
        k = 50 + 0.02 * (temperature - 20)  # W/(m·K)
        c = 480 + 0.1 * (temperature - 20)  # J/(kg·K)
        return (k, material.density, c)
    elif material.name == 'Aluminum':
        # Example coefficients for temperature-dependent properties of Aluminum
        k = 205 + 0.1 * (temperature - 20)  # W/(m·K)
        c = 897 + 0.15 * (temperature - 20)  # J/(kg·K)
        return (k, material.density, c)
    elif material.name == 'Rock Wool':
        # Rock wool is typically less sensitive to temperature
        k = 0.04  # W/(m·K)
        c = 840  # J/(kg·K)
        return (k, material.density, c)
    elif material.name == 'Fusible Link':
        # Fusible links generally have specific properties
        k = 0.15  # W/(m·K)
        c = 2000  # J/(kg·K)
        return (k, material.density, c)
    elif material.name == 'Air':
        # Air properties change with temperature
        k = 0.025 + 0.0002 * (temperature - 20)  # W/(m·K)
        c = 1005 + 0.1 * (temperature - 20)  # J/(kg·K)
        return (k, 1.225, c)  # Density of air at sea level is approximately 1.225 kg/m^3
    else:
        raise ValueError("Material not recognized.")

# Creating some materials
steel = Material('Steel', 50, 7850, 480)  # properties at 20°C
aluminum = Material('Aluminum', 205, 2700, 897)
rock_wool = Material('Rock Wool', 0.04, 100, 840)
fusible_link = Material('Fusible Link', 0.15, 200, 2000)
air = Material('Air', 0.025, 1.225, 1005)

# Example usage
if __name__ == '__main__':
    temperature = 100  # Example temperature in °C
    print(temperature_dependent_properties(steel, temperature))
    print(temperature_dependent_properties(aluminum, temperature))
    print(temperature_dependent_properties(rock_wool, temperature))
    print(temperature_dependent_properties(fusible_link, temperature))
    print(temperature_dependent_properties(air, temperature))
