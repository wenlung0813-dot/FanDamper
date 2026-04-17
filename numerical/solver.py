"""
Main coupled solver for thermal flow in fire damper
Implements SIMPLE algorithm for pressure-velocity coupling
"""

import numpy as np
from typing import Optional, Dict
from core.thermal_model import ThermalModel
from core.fluid_dynamics import FluidDynamicsModel
from core.boundary_conditions import BoundaryConditionManager
from numerical.time_integration import RungeKutta3, AdaptiveTimeStep
from numerical.discretization import FVMDiscretizer

class CoupledThermalFlowSolver:
    """
    Coupled solver for thermal flow in fire damper
    
    Solves:
    1. Navier-Stokes equations with Boussinesq buoyancy
    2. Energy equation (heat transfer)
    3. Damper response based on temperature
    """
    
    def __init__(self, domain_size: tuple, grid_points: tuple,
                 fluid_material, wall_material):
        """
        Initialize solver
        
        Args:
            domain_size: (Lx, Ly, Lz) domain dimensions [m]
            grid_points: (nx, ny, nz) grid resolution
            fluid_material: Air properties
            wall_material: Wall/damper material properties
        """
        self.domain_size = domain_size
        self.grid_points = grid_points
        
        # Initialize models
        self.fluid_model = FluidDynamicsModel(fluid_material, domain_size, grid_points)
        self.thermal_model = ThermalModel(wall_material, domain_size, grid_points)
        
        # Boundary conditions
        self.bc_manager = BoundaryConditionManager()
        
        # Discretization
        self.discretizer = FVMDiscretizer(domain_size, grid_points)
        
        # Time integration
        self.time_integrator = RungeKutta3()
        self.adaptive_dt = AdaptiveTimeStep()
        
        # Simulation state
        self.t = 0.0
        self.dt = 0.001
        self.iteration = 0
        
        # Convergence criteria
        self.velocity_tolerance = 1e-6
        self.pressure_tolerance = 1e-6
        self.temperature_tolerance = 1e-6
        self.max_iterations_simple = 10
        
        # Output storage
        self.history = {
            'time': [],
            'temperature': [],
            'velocity': [],
            'pressure': [],
            'heat_source': []
        }
    
    def initialize(self, initial_velocity: float = 0.0,
                   initial_temperature: float = 293.15,
                   initial_pressure: float = 101325.0):
        """
        Initialize flow field
        
        Args:
            initial_velocity: Initial velocity magnitude [m/s]
            initial_temperature: Initial temperature [K]
            initial_pressure: Initial pressure [Pa]
        """
        self.fluid_model.u[:, :, :] = initial_velocity
        self.thermal_model.T[:, :, :] = initial_temperature
        self.fluid_model.p[:, :, :] = initial_pressure
    
    def simple_algorithm_step(self):
        """
        SIMPLE algorithm step for pressure-velocity coupling
        
        Steps:
        1. Solve momentum equation for velocity field
        2. Solve pressure correction equation
        3. Update pressure and velocity fields
        4. Correct mass flow rates
        """
        # Get boundary conditions
        u_inlet = self.bc_manager.get_inlet_velocity(self.t)
        T_inlet = self.bc_manager.get_inlet_temperature(self.t)
        
        # Update inlet boundary conditions
        if u_inlet > 0:
            self.fluid_model.u[0, :, :] = u_inlet
            self.thermal_model.T[0, :, :] = T_inlet
        
        # Get heat source
        Q_source = self.bc_manager.get_heat_source(self.t)
        heat_source_field = np.zeros(self.grid_points)
        heat_source_field[self.grid_points[0]//2, :, :] = Q_source
        
        # Step 1: Momentum equations
        self.fluid_model.update_velocity(self.thermal_model.T, self.dt)
        
        # Step 2: Pressure correction (simplified)
        # In a full implementation, this would solve the pressure Poisson equation
        self._correct_pressure()
        
        # Step 3: Apply continuity correction
        self.fluid_model.apply_continuity_correction()
    
    def _correct_pressure(self, max_iter: int = 5):
        """
        Solve pressure correction equation
        This is a simplified implementation
        """
        for _ in range(max_iter):
            # Compute divergence of velocity
            velocity = self.fluid_model.velocity
            div_u = self.discretizer.compute_divergence(velocity)
            
            # Update pressure (simplified)
            pressure_gradient = self.discretizer.compute_gradient(self.fluid_model.p)
            correction = -0.1 * self.dt * div_u
            self.fluid_model.p += correction
    
    def solve_energy_equation(self):
        """
        Solve energy equation with current velocity field
        ∂T/∂t + ρc_p(u·∇T) = ∇·(k∇T) + Q_source
        """
        heat_source = self.bc_manager.get_heat_source(self.t)
        
        # Create heat source field
        Q_field = np.zeros(self.grid_points)
        # Place heat source in the domain (e.g., at inlet region)
        if heat_source > 0:
            Q_field[0:self.grid_points[0]//3, :, :] = heat_source
        
        # Update temperature
        velocity = self.fluid_model.velocity
        self.thermal_model.update_temperature(velocity, Q_field, self.dt, method='explicit')
    
    def step(self):
        """
        Advance simulation by one time step
        """
        # SIMPLE iteration for pressure-velocity coupling
        for simple_iter in range(self.max_iterations_simple):
            self.simple_algorithm_step()
        
        # Solve energy equation
        self.solve_energy_equation()
        
        # Update time
        self.t += self.dt
        self.iteration += 1
    
    def get_damper_closure_time(self, T_fuse: float = 343.15) -> Optional[float]:
        """
        Calculate time when damper reaches fusion temperature
        
        Args:
            T_fuse: Fusible link fusion temperature [K]
        
        Returns:
            Closure time [s] or None if not reached
        """
        T_max = np.max(self.thermal_model.T)
        if T_max >= T_fuse and len(self.history['time']) > 1:
            for i, T in enumerate(self.history['temperature']):
                if np.max(T) >= T_fuse:
                    return self.history['time'][i]
        return None
    
    def store_results(self):
        """Store current state in history"""
        self.history['time'].append(self.t)
        self.history['temperature'].append(self.thermal_model.T.copy())
        self.history['velocity'].append(self.fluid_model.velocity.copy())
        self.history['pressure'].append(self.fluid_model.p.copy())
        self.history['heat_source'].append(self.bc_manager.get_heat_source(self.t))
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics
        
        Returns:
            Dictionary with performance metrics
        """
        T_current = self.thermal_model.T
        v_current = self.fluid_model.get_velocity_magnitude()
        
        stats = {
            'time': self.t,
            'iteration': self.iteration,
            'T_max': np.max(T_current),
            'T_avg': np.mean(T_current),
            'T_min': np.min(T_current),
            'v_max': np.max(v_current),
            'v_avg': np.mean(v_current),
            'p_avg': np.mean(self.fluid_model.p)
        }
        
        return stats
    
    def run(self, t_end: float, dt: float = None, save_interval: int = 10):
        """Run simulation until end time
        
        Args:
            t_end: End time [s]
            dt: Time step [s]
            save_interval: Save results every N iterations
        """
        if dt is not None:
            self.dt = dt
        
        iteration = 0
        while self.t < t_end:
            self.step()
            
            if iteration % save_interval == 0:
                self.store_results()
                stats = self.get_statistics()
                print(f"t={stats['time']:.3f}s | T_max={stats['T_max']:.1f}K | v_max={stats['v_max']:.3f}m/s")
            
            iteration += 1
        
        return self.history