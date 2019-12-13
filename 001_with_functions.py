import bb_setup as bbs

sequence_fname = 'mad/lhc_without_bb.seq'
ip_names = ['ip1', 'ip2', 'ip5', 'ip8']

circumference = 26658.8832
harmonic_number = 35640
bunch_spacing_buckets = 10
numberOfLRPerIRSide = 21
numberOfHOSlices = 11
sigt = 0.0755

# Generate dataframes with names and location of the bb encounters (B1)
bb_df_b1 = bbs.generate_set_of_bb_encounters_1beam(
    circumference, harmonic_number,
    bunch_spacing_buckets, numberOfLRPerIRSide,
    numberOfHOSlices, sigt, ip_names,
    beam_name = 'b1',
    other_beam_name = 'b2')

# Generate dataframes with names and location of the bb encounters (B2)
bb_df_b2 = bbs.generate_set_of_bb_encounters_1beam(
    circumference, harmonic_number,
    bunch_spacing_buckets, numberOfLRPerIRSide,
    numberOfHOSlices, sigt, ip_names,
    beam_name = 'b2',
    other_beam_name = 'b1')

# Install dummy bb lenses in mad sequences
mad = bbs.build_mad_instance_with_dummy_bb(
    sequences_file_name=sequence_fname,
    bb_data_frames=[bb_df_b1, bb_df_b2],
    beam_names=['b1', 'b2'],
    sequence_names=['lhcb1', 'lhcb2'],
    mad_echo=False, mad_warn=False, mad_info=False)

# Use mad survey and twiss to get geometry and locations of all encounters
bbs.get_geometry_and_optics_b1_b2(mad, bb_df_b1, bb_df_b2)

# Get the position ot the IPs in the surveys of the two beams
ip_position_df = bbs.get_survey_ip_position_b1_b2(mad, ip_names)

# Get geometry and optics at the partner encounter
bbs.get_partner_corrected_position_and_optics(
        bb_df_b1, bb_df_b2, ip_position_df)

# Compute separation, crossing plane rotation and crossing angle
for bb_df in [bb_df_b1, bb_df_b2]:
    bbs.compute_separations(bb_df)
    bbs.compute_local_crossing_angle_and_plane(bb_df)
