===============
OpenTripPlanner
===============

Tulsa Web Devs runs an instance of `OpenTripPlanner`_ using this Tulsa Transit GTFS
feed. The following instructions explain how to update the OpenTripPlanner
graph object file at http://tripplanner.tulsawebdevs.org

Upload new feed .zip
====================
The OpenTripPlanner server can download the feed.zip from an external website,
so you just need to make it accessible.

One way is to get it on http://gtfs.tulsawebdevs.org.  You'll need a login in
order to upload files.  You can upload an MTTA signup, and a feed will be
generated in about 90 minutes.  Or, if you generate a feed locally, you can
directly upload it.  If you set the feed as the current feed, it will be
available at http://gtfs.tulsawebdevs.org/ttg/files/by_version/current/feed.zip .
This is the preferred way to load the GTFS file, since we can re-run the
importer without changing the config file.

You can also store it in dropbox, in groovecoder's `mtta_gtfs public dropbox folder`_
so the OpenTripPlanner server can download them to build its graph object.
When you generate a new feed .zip file, upload it to the
`mtta_gtfs public dropbox folder`_.

SSH to the server
=================

The server is a Rackspace 2GB instance running Ubuntu 12.04 with an 'otp' user
account running OpenTripPlanner. To connect to the box:

#. grab the `otp_rsa` private key from our `tulsa_transit folder`_ on Dropbox
   (You'll need to be invited to the folder by groovecoder)
#. Use the following ssh config::

    Host tripplanner
        HostName 50.57.172.192
        User otp
        IdentityFile ~/.ssh/otp_rsa

#. `ssh tripplanner`

Update graph-builder.xml
========================

Once you're on the box, you need to update OpenTripPlanner's builder to use the
new feed .zip file.

#. Edit `/otp/graph-builder.xml`
#. Change the GtfsBundle url value.  For gtfs.tulsawebdevs.org::

    <bean class="org.opentripplanner.graph_builder.model.GtfsBundle">
        <property name="url" value="http://gtfs.tulsawebdevs.org/ttg/files/by_version/current/feed.zip" />

or, for groovecoder's dropbox::

    <bean class="org.opentripplanner.graph_builder.model.GtfsBundle">
        <property name="url" value="https://dl.dropbox.com/u/219693365/mtta_gtfs/{new-file}.zip" />


Run build-graph.sh
==================

Now run the graph builder - it will fetch the new feed .zip file and generate a
new graph object. (May take a few minutes)::

    cd /otp/ && .bin/build-graph.sh

Restart OpenTripPlanner
=======================

OpenTripPlanner should be running in a screen session of the otp user. You need
to restart OpenTripPlanner to load the new graph object::

    screen -x
    ^C
    cd /otp && sudo .bin/start-server.sh


.. _`OpenTripPlanner`: http://opentripplanner.com/
.. _`mtta_gtfs public dropbox folder`: https://www.dropbox.com/sh/h2zfuvwcvjffkod/TFbLf7mQVf/mtta_gtfs
.. _`tulsa_transit folder`: https://www.dropbox.com/sh/4vy8gqz26txdm28/49Su57CdDU
