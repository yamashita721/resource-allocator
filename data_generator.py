import os
from data.generator import (
    generate_zones as gen_z,
    generate_disaster_status as gen_ds,
    generate_resource_inventory as gen_ri,
    generate_warehouses as gen_w,
    generate_road_network as gen_rn,
    run_all
)

def generate_zones():
    gen_z()

def generate_disaster_status():
    gen_ds()

def generate_resource_inventory():
    gen_ri()

if __name__ == "__main__":
    run_all()
