# -*- coding: utf-8 -*-
"""Giant_Music_Transformer_Training_Dataset_Maker.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FlbNJsrQlkHmOqMo7xXquomZmBQ0EHK4

# Giant Music Transformer Training Dataset Maker (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

#### Project Los Angeles

#### Tegridy Code 2023

***

# (SETUP ENVIRONMENT)
"""

#@title Install all dependencies (run only once per session)

!git clone https://github.com/asigalov61/tegridy-tools
!pip install tqdm

#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os

import math
import statistics
import random

from tqdm import tqdm

if not os.path.exists('/content/Dataset'):
    os.makedirs('/content/Dataset')

print('Loading TMIDIX module...')
os.chdir('/content/tegridy-tools/tegridy-tools')

import TMIDIX

print('Done!')

os.chdir('/content/')
print('Enjoy! :)')

"""# (DOWNLOAD SOURCE MIDI DATASET)"""

# Commented out IPython magic to ensure Python compatibility.
#@title Download original LAKH MIDI Dataset

# %cd /content/Dataset/

!wget 'http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz'
!tar -xvf 'lmd_full.tar.gz'
!rm 'lmd_full.tar.gz'

# %cd /content/

#@title Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

"""# (FILE LIST)"""

#@title Save file list
###########

print('Loading MIDI files...')
print('This may take a while on a large dataset in particular.')

dataset_addr = "/content/Dataset"
# os.chdir(dataset_addr)
filez = list()
for (dirpath, dirnames, filenames) in os.walk(dataset_addr):
    filez += [os.path.join(dirpath, file) for file in filenames]
print('=' * 70)

if filez == []:
    print('Could not find any MIDI files. Please check Dataset dir...')
    print('=' * 70)

print('Randomizing file list...')
random.shuffle(filez)

TMIDIX.Tegridy_Any_Pickle_File_Writer(filez, '/content/drive/MyDrive/filez')

#@title Load file list
filez = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/drive/MyDrive/filez')

"""# (PROCESS)"""

#@title Process MIDIs with TMIDIX MIDI processor

print('=' * 70)
print('TMIDIX MIDI Processor')
print('=' * 70)
print('Starting up...')
print('=' * 70)

###########

START_FILE_NUMBER = 0
LAST_SAVED_BATCH_COUNT = 0

input_files_count = START_FILE_NUMBER
files_count = LAST_SAVED_BATCH_COUNT

melody_chords_f = []

stats = [0] * 129

print('Processing MIDI files. Please wait...')
print('=' * 70)

for f in tqdm(filez[START_FILE_NUMBER:]):
    try:
        input_files_count += 1

        fn = os.path.basename(f)

        # Filtering out giant MIDIs
        file_size = os.path.getsize(f)

        if file_size <= 1000000:

          #=======================================================
          # START PROCESSING

          # Convering MIDI to ms score with MIDI.py module
          score = TMIDIX.midi2single_track_ms_score(open(f, 'rb').read(), recalculate_channels=False)

          # INSTRUMENTS CONVERSION CYCLE
          events_matrix = []
          itrack = 1
          patches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

          while itrack < len(score):
              for event in score[itrack]:
                  if event[0] == 'note' or event[0] == 'patch_change':
                      events_matrix.append(event)
              itrack += 1

          events_matrix.sort(key=lambda x: x[1])

          events_matrix1 = []

          for event in events_matrix:
                  if event[0] == 'patch_change':
                        patches[event[2]] = event[3]

                  if event[0] == 'note':
                        event.extend([patches[event[3]]])

                        if events_matrix1:
                            if (event[1] == events_matrix1[-1][1]):
                                if ([event[3], event[4]] != events_matrix1[-1][3:5]):
                                    events_matrix1.append(event)
                            else:
                                events_matrix1.append(event)

                        else:
                            events_matrix1.append(event)

          if len(events_matrix1) > 0:
            if min([e[1] for e in events_matrix1]) >= 0 and min([e[2] for e in events_matrix1]) >= 0:

              #=======================================================
              # PRE-PROCESSING

              # checking number of instruments in a composition
              instruments_list_without_drums = list(set([y[3] for y in events_matrix1 if y[3] != 9]))
              instruments_list = list(set([y[3] for y in events_matrix1]))

              if len(events_matrix1) > 0 and len(instruments_list_without_drums) > 0:

                # recalculating timings
                for e in events_matrix1:
                    e[1] = int(e[1] / 8) # Max 4 seconds for start-times
                    e[2] = int(e[2] / 16) # Max 4 seconds for durations

                # Sorting by patch, pitch, then by start-time
                events_matrix1.sort(key=lambda x: x[6])
                events_matrix1.sort(key=lambda x: x[4], reverse=True)
                events_matrix1.sort(key=lambda x: x[1])

                #=======================================================
                # FINAL PRE-PROCESSING

                melody_chords = []

                pe = events_matrix1[0]

                for e in events_matrix1:

                    # Cliping all values...
                    time = max(0, min(511, e[1]-pe[1]))
                    dur = max(0, min(255, e[2]))
                    cha = max(0, min(15, e[3]))
                    ptc = max(1, min(127, e[4]))

                    pat = max(0, min(127, e[6]))

                    # Calculating octo-velocity
                    vel = max(8, min(127, e[5]))
                    velocity = round(vel / 15)-1

                    # Writing final note                      :
                    melody_chords.append([time, dur, cha, ptc, pat, velocity])

                    pe = e

                #=======================================================
                # FINAL PROCESSING
                #=======================================================

                melody_chords2 = []

                # Break between compositions / Intro seq

                if 9 in instruments_list:
                  drums_present = 19715 # Yes
                else:
                  drums_present = 19714 # No

                if melody_chords[0][2] != 9:
                    pat = melody_chords[0][4]
                else:
                    pat = 128

                melody_chords2.extend([19845, drums_present, 19716+pat]) # Intro seq

                #=======================================================

                # TOTAL DICTIONARY SIZE 19846+1=19847

                #=======================================================
                # MAIN PROCESSING CYCLE
                #=======================================================

                chords_counter = 1

                comp_chords_len = len([y for y in melody_chords if y[0] != 0])

                for m in melody_chords:

                    if ((comp_chords_len - chords_counter) == 50) and (m[0] != 0):
                        melody_chords2.extend([19713, 19713, 19713]) # Outro token seq

                    if (chords_counter % 100 == 0) and (m[0] != 0):
                        nct = 19201+min(511, ((chords_counter // 100)-1)) # chords counter token
                        melody_chords2.extend([nct, nct, nct])
                        chords_counter += 1
                    else:
                        if m[0] != 0:
                            chords_counter += 1

                    # Drums patch
                    if m[2] == 9: # Drums patch will be == 128
                        pat = 128
                    else:
                        pat = m[4]

                    cha_pat = (129 * pat) + m[3]

                    dur_vel = (8 * m[1]) + m[5]

                    melody_chords2.extend([m[0], dur_vel+512, cha_pat+2560])

                    stats[pat] += 1 # Patches stats

                melody_chords2.extend([19846, 19846, 19846]) # EOS

                melody_chords_f.append(melody_chords2)

                #=======================================================

                # Processed files counter
                files_count += 1

                # Saving every 5000 processed files
                if files_count % 2500 == 0:
                  print('SAVING !!!')
                  print('=' * 70)
                  print('Saving processed files...')
                  print('=' * 70)
                  print('Data check:', min(melody_chords_f[0]), '===', max(melody_chords_f[0]), '===', len(list(set(melody_chords_f[0]))), '===', len(melody_chords_f[0]))
                  print('=' * 70)
                  print('Processed so far:', files_count, 'out of', input_files_count, '===', files_count / input_files_count, 'good files ratio')
                  print('=' * 70)
                  count = str(files_count)
                  TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/content/drive/MyDrive/LAKH_INTs_'+count)
                  melody_chords_f = []
                  print('=' * 70)

    except KeyboardInterrupt:
        print('Saving current progress and quitting...')
        break

    except Exception as ex:
        print('WARNING !!!')
        print('=' * 70)
        print('Bad MIDI:', f)
        print('Error detected:', ex)
        print('=' * 70)
        continue

# Saving last processed files...
print('=' * 70)
print('Saving processed files...')
print('=' * 70)
print('Data check:', min(melody_chords_f[0]), '===', max(melody_chords_f[0]), '===', len(list(set(melody_chords_f[0]))), '===', len(melody_chords_f[0]))
print('=' * 70)
print('Processed so far:', files_count, 'out of', input_files_count, '===', files_count / input_files_count, 'good files ratio')
print('=' * 70)
count = str(files_count)
TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/content/drive/MyDrive/LAKH_INTs_'+count)

# Displaying resulting processing stats...
print('=' * 70)
print('Done!')
print('=' * 70)

print('Resulting Stats:')
print('=' * 70)
print('Total good processed MIDI files:', files_count)
print('=' * 70)

print('Instruments stats:')
print('=' * 70)
print('Piano:', stats[0])
print('Drums:', stats[128])
print('=' * 70)

"""# (TEST INTS)"""

#@title Test INTs

train_data1 = random.choice(melody_chords_f)

print('Sample INTs', train_data1[:15])

out = train_data1

if len(out) != 0:

    song = out
    song_f = []

    time = 0
    dur = 0
    vel = 90
    pitch = 0
    channel = 0

    patches = [-1] * 16

    channels = [0] * 16
    channels[9] = 1

    for ss in song:

        if 0 <= ss < 512:

            time += (ss * 8)

        if 512 <= ss < 2560:

            dur = ((ss-512) // 8) * 16
            vel = (((ss-512) % 8)+1) * 15

        if 2560 <= ss < 19201:
            patch = (ss-2560) // 129

            if patch < 128:

                if patch not in patches:
                  if 0 in channels:
                      cha = channels.index(0)
                      channels[cha] = 1
                  else:
                      cha = 15

                  patches[cha] = patch
                  channel = patches.index(patch)
                else:
                  channel = patches.index(patch)

            if patch == 128:
                channel = 9


            pitch = (ss-2560) % 129

            song_f.append(['note', time, dur, channel, pitch, vel ])

patches = [0 if x==-1 else x for x in patches]

detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                          output_signature = 'Giant Music Transformer',
                                                          output_file_name = '/content/Giant-Music-Composition',
                                                          track_name='Project Los Angeles',
                                                          list_of_MIDI_patches=patches
                                                          )

print('Done!')

"""# Congrats! You did it! :)"""