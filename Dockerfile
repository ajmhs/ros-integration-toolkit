# (c) 2025 Copyright, Real-Time Innovations, Inc.  All rights reserved.
# RTI grants Licensee a license to use, modify, compile, and create derivative
# works of the Software.  Licensee has the right to distribute object form only
# for use with RTI products.  The Software is provided "as is", with no warranty
# of any type, including any warranty for fitness for any purpose. RTI is under
# no obligation to maintain or support the Software.  RTI shall not be liable
# for any incidental or consequential damages arising out of the use or
# inability to use the software.

# The Dockerfile is based on the official ROS2 image for the Kilted Kaiju release. 
#
# To build the Docker image, run the following command from the root repository folder:
#   docker build -t ros2:rti-toolkit .
#
# To run the Docker container, run the following command:
#   docker run -it --rm -v "./exported_idls:/exported_idls" ros2:rti-toolkit
#
#   The -it option is used to run the container in interactive mode.
#   The --rm option is used to remove the container when it exits.
#
# The container will start and run the bash shell interactively

# Use the latest stable ROS2 release (Kilted Kaiju)
FROM ros:kilted

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=kilted

# Install Python and essential tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    ssh \
    && rm -rf /var/lib/apt/lists/*

# Create a workspace directory
WORKDIR /ros2_ws

# Clone the specific branch from the repository
RUN git clone -b ajmh_process_comments \
    https://github.com/ajmhs/ros-integration-toolkit.git

# Source ROS2 setup in bashrc for convenience
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws/ros-integration-toolkit

# Run the headless scan script on container start, exporting IDL files to /exported_idls excluding dds_ namespace
CMD ["/usr/bin/python3", "scan_headless.py", "/exported_idls", "False"]

