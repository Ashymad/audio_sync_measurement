/*
 * Example of using commands - asynchronous input
 * Part of Comedilib
 *
 * Copyright (c) 1999,2000,2001 David A. Schleef <ds@schleef.org>
 *
 * This file may be freely modified, distributed, and combined with
 * other software, as long as proper attribution is given in the
 * source code.
 */

/*
 * An example for directly using Comedi commands.  Comedi commands
 * are used for asynchronous acquisition, with the timing controlled
 * by on-board timers or external events.
 */

#include <stdio.h>
#include <comedilib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <hdf5.h>
#include "examples.h"

#define N_CHANS 256
static unsigned int chanlist[N_CHANS];
static comedi_range * range_info[N_CHANS];
static lsampl_t maxdata[N_CHANS];


int prepare_cmd_lib(comedi_t *dev, int subdevice, int n_scan, int n_chan, unsigned period_nanosec, comedi_cmd *cmd);

void do_cmd(comedi_t *dev,comedi_cmd *cmd);

void print_datum(lsampl_t raw, int channel_index, short physical);

char *cmdtest_messages[]={
	"success",
	"invalid source",
	"source conflict",
	"invalid argument",
	"argument conflict",
	"invalid chanlist",
};

int main(int argc, char *argv[])
{
	comedi_t *dev;
	comedi_cmd c,*cmd=&c;
	int ret;
	int total=0;
	int i;
	struct timeval start,end;
	int subdev_flags;
	lsampl_t raw;
	struct parsed_options options;

	init_parsed_options(&options);
	options.subdevice = -1;
	parse_options(&options, argc, argv);
	if(options.n_chan > N_CHANS){
		options.n_chan = N_CHANS;
	}

	/* The following variables used in this demo
	 * can be modified by command line
	 * options.  When modifying this demo, you may want to
	 * change them here. */
	//options.filename = "/dev/comedi0";
	//options.subdevice = 0;
	//options.channel = 0;
	//options.range = 0;
	//options.aref = AREF_GROUND;
	//options.n_chan = 4;
	//options.n_scan = 1000;
	//options.freq = 1000.0;

	/* open the device */
	dev = comedi_open(options.filename);
	if(!dev){
		comedi_perror(options.filename);
		exit(1);
	}

	if(options.subdevice < 0) {
		/* Subdevice not set on command line. */
		/* Default to the 'read' subdevice (if any). */
		options.subdevice = comedi_get_read_subdevice(dev);
		if(options.subdevice < 0) {
			/* No 'read' subdevice, so default to 0 instead. */
			options.subdevice = 0;
		}
		fprintf(stderr, "defaulted to subdevice %d\n", options.subdevice);
	}

	/* Check subdevice exists. */
	ret = comedi_get_n_subdevices(dev);
	if(ret <= options.subdevice){
		fprintf(stderr, "subdevice %d does not exist\n", options.subdevice);
		exit(1);
	}

	/* Check subdevice supports 'read' commands. */
	ret = comedi_get_subdevice_flags(dev, options.subdevice);
	if(ret < 0 || !(ret & SDF_CMD_READ)) {
		fprintf(stderr, "subdevice %d does not support 'read' commands\n", options.subdevice);
		exit(1);
	}

	// Print numbers for clipped inputs
	comedi_set_global_oor_behavior(COMEDI_OOR_NUMBER);

	/* Set up channel list */
	for(i = 0; i < options.n_chan; i++){
		chanlist[i] = CR_PACK(options.channel + i, options.range, options.aref);
		range_info[i] = comedi_get_range(dev, options.subdevice, options.channel, options.range);
		maxdata[i] = comedi_get_maxdata(dev, options.subdevice, options.channel);
	}

	/* prepare_cmd_lib() uses a Comedilib routine to find a
	 * good command for the device.  prepare_cmd() explicitly
	 * creates a command, which may not work for your device. */
	ret = prepare_cmd_lib(dev, options.subdevice, options.n_scan, options.n_chan, 1e9 / options.freq, cmd);
	//ret = prepare_cmd(dev, options.subdevice, options.n_scan, options.n_chan, 1e9 / options.freq, cmd);
	if(ret < 0){
		exit(1);
	}

	fprintf(stderr, "command before testing:\n");
	dump_cmd(stderr, cmd);

	/* comedi_command_test() tests a command to see if the
	 * trigger sources and arguments are valid for the subdevice.
	 * If a trigger source is invalid, it will be logically ANDed
	 * with valid values (trigger sources are actually bitmasks),
	 * which may or may not result in a valid trigger source.
	 * If an argument is invalid, it will be adjusted to the
	 * nearest valid value.  In this way, for many commands, you
	 * can test it multiple times until it passes.  Typically,
	 * if you can't get a valid command in two tests, the original
	 * command wasn't specified very well. */
	ret = comedi_command_test(dev, cmd);
	if(ret < 0){
		comedi_perror("comedi_command_test");
		if(errno == EIO){
			fprintf(stderr,"Ummm... this subdevice doesn't support commands\n");
		}
		exit(1);
	}
	fprintf(stderr,"first test returned %d (%s)\n", ret,
			cmdtest_messages[ret]);
	dump_cmd(stderr, cmd);

	ret = comedi_command_test(dev, cmd);
	if(ret < 0){
		comedi_perror("comedi_command_test");
		exit(1);
	}
	fprintf(stderr,"second test returned %d (%s)\n", ret,
			cmdtest_messages[ret]);
	if(ret!=0){
		dump_cmd(stderr, cmd);
		fprintf(stderr, "Error preparing command\n");
		exit(1);
	}

	comedi_set_read_subdevice(dev, cmd->subdev);
	ret = comedi_get_read_subdevice(dev);
	if (ret < 0 || ret != cmd->subdev) {
		fprintf(stderr,
			"failed to change 'read' subdevice from %d to %d\n",
			ret, cmd->subdev);
		exit(1);
	}

    size_t sample_size;
    if(subdev_flags & SDF_LSAMPL)
        sample_size = sizeof(lsampl_t);
    else
        sample_size = sizeof(sampl_t);

    const size_t BUFSZ = options.n_chan * 10000 * sample_size;
    void * buf = malloc(BUFSZ);


    hid_t  file_id, dataset_id, dataspace_id; /* identifiers */
    herr_t status;

    file_id = H5Fcreate("out.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    const hsize_t h5size[] = {options.n_scan, options.n_chan};
    dataspace_id = H5Screate_simple (2, h5size, h5size);
    dataset_id = H5Dcreate(file_id, "/dset", H5T_STD_U16LE, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);

	/* this is only for informational purposes */
	gettimeofday(&start, NULL);
	fprintf(stderr,"start time: %ld.%06ld\n", start.tv_sec, start.tv_usec);

	/* start the command */
	ret = comedi_command(dev, cmd);
	if(ret < 0){
		comedi_perror("comedi_command");
		exit(1);
	}
	subdev_flags = comedi_get_subdevice_flags(dev, options.subdevice);
	while(1){
		ret = read(comedi_fileno(dev),buf,BUFSZ);
		if(ret < 0){
			/* some error occurred */
			perror("read");
			break;
		}else if(ret == 0){
			/* reached stop condition */
			break;
		}else{
			static int col = 0;
            const hsize_t blockstride[] = {1, 1};
            const hsize_t count[] = {ret/(options.n_chan*sample_size), options.n_chan};
            const hsize_t offset[] = {total/(options.n_chan*sample_size), 0};
            const hsize_t memsize[] = {ret/sample_size};
            hid_t memspace_id = H5Screate_simple(1, memsize, memsize);
            status = H5Sselect_hyperslab(dataspace_id, H5S_SELECT_SET, offset, blockstride, count, blockstride);
            //printf("Returned: %i, Sample size: %i\n", ret, sample_size);
            //printf("Count: [%i, %i], Offset: [%i, %i], Elements: %i\n", count[0], count[1], offset[0], offset[1], memsize[0]);
            //printf("Elements: [");
            //for (int i = 0; i < memsize[0]; i++) {
            //    if(subdev_flags & SDF_LSAMPL)
            //        printf("%i, ", ((lsampl_t *)buf)[i]);
            //    else
            //        printf("%i, ", ((sampl_t *)buf)[i]);
            //}
            //printf("]\n");
            status = H5Dwrite(dataset_id, H5T_STD_U16LE, memspace_id, dataspace_id, H5P_DEFAULT, buf);
			total += ret;
		}
	}


	/* this is only for informational purposes */
	gettimeofday(&end,NULL);
	fprintf(stderr,"end time: %ld.%06ld\n", end.tv_sec, end.tv_usec);

    /* Close the file. */
    status = H5Dclose(dataset_id);
    status = H5Fclose(file_id);

	end.tv_sec -= start.tv_sec;
	if(end.tv_usec < start.tv_usec){
		end.tv_sec--;
		end.tv_usec += 1000000;
	}
	end.tv_usec -= start.tv_usec;
	fprintf(stderr,"time: %ld.%06ld\n", end.tv_sec, end.tv_usec);

	return 0;
}

/*
 * This prepares a command in a pretty generic way.  We ask the
 * library to create a stock command that supports periodic
 * sampling of data, then modify the parts we want. */
int prepare_cmd_lib(comedi_t *dev, int subdevice, int n_scan, int n_chan, unsigned scan_period_nanosec, comedi_cmd *cmd)
{
	int ret;

	memset(cmd,0,sizeof(*cmd));

	/* This comedilib function will get us a generic timed
	 * command for a particular board.  If it returns -1,
	 * that's bad. */
	ret = comedi_get_cmd_generic_timed(dev, subdevice, cmd, n_chan, scan_period_nanosec);
	if(ret<0){
		fprintf(stderr,"comedi_get_cmd_generic_timed failed\n");
		return ret;
	}

	/* Modify parts of the command */
	cmd->chanlist = chanlist;
	cmd->chanlist_len = n_chan;
	if(cmd->stop_src == TRIG_COUNT) cmd->stop_arg = n_scan;

	return 0;
}

/*
 * Set up a command by hand.  This will not work on some devices.
 * There is no single command that will work on all devices.
 */
int prepare_cmd(comedi_t *dev, int subdevice, int n_scan, int n_chan, unsigned period_nanosec, comedi_cmd *cmd)
{
	memset(cmd,0,sizeof(*cmd));

	/* the subdevice that the command is sent to */
	cmd->subdev =	subdevice;

	/* flags */
	cmd->flags = 0;

	/* Wake up at the end of every scan */
	//cmd->flags |= TRIG_WAKE_EOS;

	/* Use a real-time interrupt, if available */
	//cmd->flags |= TRIG_RT;

	/* each event requires a trigger, which is specified
	   by a source and an argument.  For example, to specify
	   an external digital line 3 as a source, you would use
	   src=TRIG_EXT and arg=3. */

	/* The start of acquisition is controlled by start_src.
	 * TRIG_NOW:     The start_src event occurs start_arg nanoseconds
	 *               after comedi_command() is called.  Currently,
	 *               only start_arg=0 is supported.
	 * TRIG_FOLLOW:  (For an output device.)  The start_src event occurs
	 *               when data is written to the buffer.
	 * TRIG_EXT:     start event occurs when an external trigger
	 *               signal occurs, e.g., a rising edge of a digital
	 *               line.  start_arg chooses the particular digital
	 *               line.
	 * TRIG_INT:     start event occurs on a Comedi internal signal,
	 *               which is typically caused by an INSN_TRIG
	 *               instruction.
	 */
	cmd->start_src =	TRIG_NOW;
	cmd->start_arg =	0;

	/* The timing of the beginning of each scan is controlled by
	 * scan_begin.
	 * TRIG_TIMER:   scan_begin events occur periodically.
	 *               The time between scan_begin events is
	 *               convert_arg nanoseconds.
	 * TRIG_EXT:     scan_begin events occur when an external trigger
	 *               signal occurs, e.g., a rising edge of a digital
	 *               line.  scan_begin_arg chooses the particular digital
	 *               line.
	 * TRIG_FOLLOW:  scan_begin events occur immediately after a scan_end
	 *               event occurs.
	 * The scan_begin_arg that we use here may not be supported exactly
	 * by the device, but it will be adjusted to the nearest supported
	 * value by comedi_command_test(). */
	cmd->scan_begin_src =	TRIG_TIMER;
	cmd->scan_begin_arg = period_nanosec;		/* in ns */

	/* The timing between each sample in a scan is controlled by convert.
	 * TRIG_TIMER:   Conversion events occur periodically.
	 *               The time between convert events is
	 *               convert_arg nanoseconds.
	 * TRIG_EXT:     Conversion events occur when an external trigger
	 *               signal occurs, e.g., a rising edge of a digital
	 *               line.  convert_arg chooses the particular digital
	 *               line.
	 * TRIG_NOW:     All conversion events in a scan occur simultaneously.
	 * Even though it is invalid, we specify 1 ns here.  It will be
	 * adjusted later to a valid value by comedi_command_test() */
	cmd->convert_src =	TRIG_TIMER;
	cmd->convert_arg =	1;		/* in ns */

	/* The end of each scan is almost always specified using
	 * TRIG_COUNT, with the argument being the same as the
	 * number of channels in the chanlist.  You could probably
	 * find a device that allows something else, but it would
	 * be strange. */
	cmd->scan_end_src =	TRIG_COUNT;
	cmd->scan_end_arg =	n_chan;		/* number of channels */

	/* The end of acquisition is controlled by stop_src and
	 * stop_arg.
	 * TRIG_COUNT:  stop acquisition after stop_arg scans.
	 * TRIG_NONE:   continuous acquisition, until stopped using
	 *              comedi_cancel()
	 * */
	cmd->stop_src =		TRIG_COUNT;
	cmd->stop_arg =		n_scan;

	/* the channel list determined which channels are sampled.
	   In general, chanlist_len is the same as scan_end_arg.  Most
	   boards require this.  */
	cmd->chanlist =		chanlist;
	cmd->chanlist_len =	n_chan;

	return 0;
}

void print_datum(lsampl_t raw, int channel_index, short physical) {
	double physical_value;
	if(!physical) {
		printf("%d ",raw);
	} else {
		physical_value = comedi_to_phys(raw, range_info[channel_index], maxdata[channel_index]);
		printf("%#8.6g ",physical_value);
	}
}
