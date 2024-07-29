# Hello World Tutorial

## View on Youtube:
[![Hello World](https://img.youtube.com/vi/_wGZxmQclFA/0.jpg)](https://www.youtube.com/watch?v=_wGZxmQclFA)

# Build the dev image
```
docker build -t nvflare-pt -f Dockerfile-dev .
```

# Run the container
## Linux/Mac:
```
./dockerRun.sh
```
## Windows:
```
docker run --rm -it ^
    --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 ^
    --name flare ^
    -v %cd%:/workspace ^
    -w //workspace ^
    nvflare-pt:latest
```

# Run the simulator
```
nvflare simulator -c site1,site2 ./jobs/job
```

# View the results
Navigate to:
```
./test_results/simulate_job
```