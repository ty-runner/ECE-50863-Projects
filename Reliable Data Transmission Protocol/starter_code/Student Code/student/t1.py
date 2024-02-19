import subprocess
import time

# Define the commands
commands = [
    "cd ..",
    "cd ..",
    "cd ./Emulator",
    "py emulator.py ../TestConfig/config1.ini",
    "cd ../StudentCode/student",
    "make run-receiver config=./TestConfig/config1.ini",
    "sleep 2",  # Wait for 2 seconds
    "make run-sender config=./TestConfig/config1.ini"
]

# Execute each command
for command in commands:
    # For commands with arguments, split the command into a list
    command_list = command.split()
    
    # Execute the command
    subprocess.run(command_list)

    # If the command is not the last one, wait for 2 seconds
    if command != commands[-1]:
        time.sleep(2)
