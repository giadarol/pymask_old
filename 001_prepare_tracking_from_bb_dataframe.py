# %%
import gc
import pickle

import numpy as np
from scipy.constants import c as clight

import bb_setup as bbs


bb_data_frames_fname = 'bb_dataframes.pkl'

generate_pysixtrack_lines = True
generate_sixtrack_inputs = True

closed_orbit_to_pysixtrack_from_mad = True

reference_bunch_charge_sixtrack_ppb = 1.2e11

sequences_to_be_tracked = [
        {'name': 'beam1_tuned', 'fname' : 'mad/lhc_without_bb_fortracking.seq', 'beam': 'b1', 'seqname':'lhcb1', 'bb_df':'bb_df_b1'},
        #{'name': 'beam4_tuned', 'fname' : 'mad/lhcb4_without_bb_fortracking.seq', 'beam': 'b2', 'seqname':'lhcb2', 'bb_df':'bb_df_b4'},
       ]

with open(bb_data_frames_fname, 'rb') as fid:
    bb_df_dict = pickle.load(fid)

# Mad model of the machines to be tracked
for ss in sequences_to_be_tracked:

    bb_df =  bb_df_dict[ss['bb_df']]

    mad_track = bbs.build_mad_instance_with_bb(
        sequences_file_name=ss['fname'],
        bb_data_frames=[bb_df],
        beam_names=[ss['beam']],
        sequence_names=[ss['seqname']],
        mad_echo=False, mad_warn=False, mad_info=False)

    # disable bb in mad model
    mad_track.globals.on_bb_switch = 0

    # Twiss and get closed-orbit
    mad_track.use(sequence=ss['seqname'])
    twiss_table = mad_track.twiss()

    beta0 = mad_track.sequence[ss['seqname']].beam.beta
    gamma0 = mad_track.sequence[ss['seqname']].beam.gamma
    p0c_eV = mad_track.sequence[ss['seqname']].beam.pc*1.e9

    x_CO  = twiss_table.x[0]
    px_CO = twiss_table.px[0]
    y_CO  = twiss_table.y[0]
    py_CO = twiss_table.py[0]
    t_CO  = twiss_table.t[0]
    pt_CO = twiss_table.pt[0]
    #convert tau, pt to sigma,delta
    sigma_CO = beta0 * t_CO
    delta_CO = ((pt_CO**2 + 2*pt_CO/beta0) + 1)**0.5 - 1

    mad_CO = np.array([x_CO, px_CO, y_CO, py_CO, sigma_CO, delta_CO])

    optics_at_start_ring = {
            'betx': twiss_table.betx[0],
            'bety': twiss_table.betx[0]}

    if generate_pysixtrack_lines:
        # Build pysixtrack model
        import pysixtrack
        line_for_tracking = pysixtrack.Line.from_madx_sequence(
            mad_track.sequence[ss['seqname']])

        bbs.setup_beam_beam_in_line(line_for_tracking, bb_df, bb_coupling=False)

        # Temporary fix due to bug in loader
        cavities, _ = line_for_tracking.get_elements_of_type(
                pysixtrack.elements.Cavity)
        for cc in cavities:
            cc.frequency = bb_df_dict['temp_rf_frequency']

        line_for_tracking.disable_beambeam()
        part_on_CO = line_for_tracking.find_closed_orbit(
            guess=mad_CO, p0c=p0c_eV,
            method={True: 'get_guess', False: 'Nelder-Mead'}[closed_orbit_to_pysixtrack_from_mad])
        line_for_tracking.enable_beambeam()

        with open(f"line_{ss['name']}_from_mad.pkl", "wb") as fid:
            linedct = line_for_tracking.to_dict(keepextra=True)
            linedct['particle_on_closed_orbit'] = part_on_CO.to_dict()
            linedct['optics_at_start_ring'] = optics_at_start_ring
            pickle.dump(linedct, fid)

        line_for_tracking.beambeam_store_closed_orbit_and_dipolar_kicks(
            part_on_CO,
            separation_given_wrt_closed_orbit_4D=True,
            separation_given_wrt_closed_orbit_6D=True)

        with open(f"line_{ss['name']}_from_mad_with_dip_correction.pkl", "wb") as fid:
            linedct = line_for_tracking.to_dict(keepextra=True)
            linedct['particle_on_closed_orbit'] = part_on_CO.to_dict()
            linedct['optics_at_start_ring'] = optics_at_start_ring
            pickle.dump(linedct, fid)

    if generate_sixtrack_inputs:
        six_fol_name = f"sixtrack_input_{ss['name']}"
#        os.mkdir(sixfolname)

        sxt_df_4d = bb_df[bb_df['label']=='bb_lr'].copy()
        sxt_df_4d['h-sep [mm]'] = -sxt_df_4d['separation_x']*1e3
        sxt_df_4d['v-sep [mm]'] = -sxt_df_4d['separation_y']*1e3
        sxt_df_4d['strength'] = sxt_df_4d['other_charge_ppb']/reference_bunch_charge_sixtrack_ppb
        sxt_df_4d['4dSxx [mm*mm]'] = sxt_df_4d['other_Sigma_11']*1e6
        sxt_df_4d['4dSyy [mm*mm]'] = sxt_df_4d['other_Sigma_33']*1e6
        sxt_df_4d['4dSxy [mm*mm]'] = sxt_df_4d['other_Sigma_13']*1e6

        sxt_df_6d = bb_df[bb_df['label']=='bb_ho'].copy()
        sxt_df_6d['h-sep [mm]'] = -sxt_df_6d['separation_x']*1e3
        sxt_df_6d['v-sep [mm]'] = -sxt_df_6d['separation_y']*1e3
        sxt_df_6d['strength'] = sxt_df_6d['other_charge_ppb']/reference_bunch_charge_sixtrack_ppb
        sxt_df_6d['Sxx [mm*mm]'] = sxt_df_6d['other_Sigma_11'] *1e6
        sxt_df_6d['Sxxp [mm*mrad]'] = sxt_df_6d['other_Sigma_12'] *1e6
        sxt_df_6d['Sxpxp [mrad*mrad]'] = sxt_df_6d['other_Sigma_22'] *1e6
        sxt_df_6d['Syy [mm*mm]'] = sxt_df_6d['other_Sigma_33'] *1e6
        sxt_df_6d['Syyp [mm*mrad]'] = sxt_df_6d['other_Sigma_34'] *1e6
        sxt_df_6d['Sypyp [mrad*mrad]'] = sxt_df_6d['other_Sigma_44'] *1e6
        sxt_df_6d['Sxy [mm*mm]'] = sxt_df_6d['other_Sigma_13'] *1e6
        sxt_df_6d['Sxyp [mm*mrad]'] = sxt_df_6d['other_Sigma_14'] *1e6
        sxt_df_6d['Sxpy [mrad*mm]'] = sxt_df_6d['other_Sigma_23'] *1e6
        sxt_df_6d['Sxpyp [mrad*mrad]'] = sxt_df_6d['other_Sigma_24'] *1e6
        #with(sixfolname + 'fc.3', 'wb'):



    # del(mad_track)
    # gc.collect()

# %%
