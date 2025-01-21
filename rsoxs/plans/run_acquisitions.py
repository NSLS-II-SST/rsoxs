##


def run_acquisitions_single(
        acquisition
        dryrun = True
):
    
    print("Loading instrument configuration: " + str(acquisition["configuration_instrument"]))
    if dryrun == False: yield from load_configuration(acquisition["configuration_instrument"])

    ## TODO: set up diodes to high or low gain

    print("Loading sample: " + str(acquisition["sample_id"]))
    if dryrun == False: yield from load_sample(acquisition["sample_id"])

    ## TODO: set temperature if needed

    print("Running scan: " + str(acquisition["plan_name"]))
    if dryrun == False: 
        if acquisition["plan_name"] == nexafs_step: yield from variable_energy_scan(acquisition["energy_parameters"])
    



def run_acquisitions_queue(
        dryrun = True
        ):
    ## Run a series of single acquisitions
    ## TODO: combine dry run and actual run into a single function for more realistic dry run

    print("Starting queue")

    queue = []

    for index, acquisition in enumerate(queue):
        run_acquisitions_single(acquisition=acquisition, dryrun=dryrun)