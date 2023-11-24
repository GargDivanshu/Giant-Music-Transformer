# -*- coding: utf-8 -*-
"""Giant_Music_Transformer_TTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wZucAs9zl2obNJAhuPQEEgYCusv_gmiI

# Giant Music Transformer TTM (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2023

***

# (GPU CHECK)
"""

#@title NVIDIA GPU check
!nvidia-smi

"""# (SETUP ENVIRONMENT)"""

#@title Install dependencies
!git clone --depth 1 https://github.com/asigalov61/Giant-Music-Transformer
!pip install huggingface_hub
!pip install torch
!pip install einops
!pip install fuzzywuzzy[speedup]
!pip install torch-summary
!pip install tqdm
!pip install matplotlib
!apt install fluidsynth #Pip does not work for some reason. Only apt works

# Commented out IPython magic to ensure Python compatibility.
#@title Import modules

print('=' * 70)
print('Loading core Giant Music Transformer modules...')

import os
import pickle
import secrets
import statistics
from time import time
import tqdm

print('=' * 70)
print('Loading main Giant Music Transformer modules...')
import torch

# %cd /content/Giant-Music-Transformer

import TMIDIX

from midi_to_colab_audio import midi_to_colab_audio

from x_transformer_1_23_2 import *

import random

from fuzzywuzzy import process

# %cd /content/
print('=' * 70)
print('Loading aux Giant Music Transformer modules...')

import matplotlib.pyplot as plt

from torchsummary import summary
from sklearn import metrics

from IPython.display import Audio, display

from huggingface_hub import hf_hub_download

from google.colab import files

print('=' * 70)
print('Done!')
print('Enjoy! :)')
print('=' * 70)

"""# (LOAD MODEL)"""

#@title Load Giant Music Transformer Large Model

#@markdown Very fast model, 32 layers, 405k MIDIs training corpus

full_path_to_model_checkpoint = "/content/Giant-Music-Transformer/Models/Large/Giant_Music_Transformer_Large_Trained_Model_36074_steps_0.3067_loss_0.927_acc.pth" #@param {type:"string"}

#@markdown Model precision option

model_precision = "bfloat16" # @param ["bfloat16", "float16"]

#@markdown bfloat16 == Half precision/faster speed (if supported, otherwise the model will default to float16)

#@markdown float16 == Full precision/fast speed

plot_tokens_embeddings = False # @param {type:"boolean"}

print('=' * 70)
print('Loading Giant Music Transformer Large Pre-Trained Model...')
print('Please wait...')
print('=' * 70)

if os.path.isfile(full_path_to_model_checkpoint):
  print('Model already exists...')

else:
  hf_hub_download(repo_id='asigalov61/Giant-Music-Transformer',
                  filename='Giant_Music_Transformer_Large_Trained_Model_36074_steps_0.3067_loss_0.927_acc.pth',
                  local_dir='/content/Giant-Music-Transformer/Models/Large',
                  local_dir_use_symlinks=False)

print('=' * 70)
print('Instantiating model...')

torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
device_type = 'cuda'

if model_precision == 'bfloat16' and torch.cuda.is_bf16_supported():
  dtype = 'bfloat16'
else:
  dtype = 'float16'

if model_precision == 'float16':
  dtype = 'float16'

ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = torch.amp.autocast(device_type=device_type, dtype=ptdtype)

SEQ_LEN = 8192

# instantiate the model

model = TransformerWrapper(
    num_tokens = 19464,
    max_seq_len = SEQ_LEN,
    attn_layers = Decoder(dim = 1024, depth = 32, heads = 32, attn_flash = True)
)

model = AutoregressiveWrapper(model, ignore_index=19463)

model.cuda()
print('=' * 70)

print('Loading model checkpoint...')

model.load_state_dict(torch.load(full_path_to_model_checkpoint))
print('=' * 70)

model.eval()

print('Done!')
print('=' * 70)

print('Model will use', dtype, 'precision...')
print('=' * 70)

# Model stats
print('Model summary...')
summary(model)

# Plot Token Embeddings
if plot_tokens_embeddings:
  tok_emb = model.net.token_emb.emb.weight.detach().cpu().tolist()

  cos_sim = metrics.pairwise_distances(
    tok_emb, metric='cosine'
  )
  plt.figure(figsize=(7, 7))
  plt.imshow(cos_sim, cmap="inferno", interpolation="nearest")
  im_ratio = cos_sim.shape[0] / cos_sim.shape[1]
  plt.colorbar(fraction=0.046 * im_ratio, pad=0.04)
  plt.xlabel("Position")
  plt.ylabel("Position")
  plt.tight_layout()
  plt.plot()
  plt.savefig("/content/Giant-Music-Transformer-Large-Tokens-Embeddings-Plot.png", bbox_inches="tight")

"""# (LOAD AUX DATA)"""

#@title Load Giant Music Transformer Aux Data

print('=' * 70)
print('Loading Giant Music Transformer Aux Data...')
print('Please wait...')
print('=' * 70)

if os.path.isfile('/content/Giant-Music-Transformer/Aux-Data/Giant_Music_Transformer_Aux_Data.pickle'):
  print('Aux Data already exists...')

else:
  hf_hub_download(repo_id='asigalov61/Giant-Music-Transformer',
                  filename='Giant_Music_Transformer_Aux_Data.pickle',
                  local_dir='/content/Giant-Music-Transformer/Aux-Data',
                  local_dir_use_symlinks=False)

print('=' * 70)
AUX_DATA = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/Giant-Music-Transformer/Aux-Data/Giant_Music_Transformer_Aux_Data')

print('Done!')
print('=' * 70)

"""# (GENERATE)"""

#@title Standard Continuation

#@markdown Text-To-Music Settings

#@markdown NOTE: You can enter any desired title or artist, or both

enter_desired_song_title = "Family Guy" #@param {type:"string"}
enter_desired_artist = "TV Themes" #@param {type:"string"}

#@markdown Generation settings

try_to_generate_outro = False #@param {type:"boolean"}
number_of_tokens_to_generate = 600 # @param {type:"slider", min:30, max:8190, step:3}
number_of_batches_to_generate = 4 #@param {type:"slider", min:1, max:16, step:1}
temperature = 0.9 # @param {type:"slider", min:0.1, max:1, step:0.05}

#@markdown Other settings
allow_model_to_stop_generation_if_needed = False #@param {type:"boolean"}
render_MIDI_to_audio = True # @param {type:"boolean"}

print('=' * 70)
print('Giant Music Transformer TTM Model Generator')
print('=' * 70)

print('Searching titles...Please wait...')
random.shuffle(AUX_DATA)

titles_index = []

for A in AUX_DATA:
  titles_index.append(A[0])

search_string = ''

if enter_desired_song_title != '' and enter_desired_artist != '':
  search_string = enter_desired_song_title + ' --- ' + enter_desired_artist

else:
  search_string = enter_desired_song_title + enter_desired_artist

search_match = process.extract(query=search_string, choices=titles_index, limit=1)
search_index = titles_index.index(search_match[0][0])

print('Done!')
print('=' * 70)
print('Selected title:', AUX_DATA[search_index][0])
print('=' * 70)

if allow_model_to_stop_generation_if_needed:
  min_stop_token = 19462
else:
  min_stop_token = None

outy = AUX_DATA[search_index][1]

block_marker = sum([(y * 16) for y in outy if y < 256]) / 1000

if try_to_generate_outro:
  outy.extend([18945])

inp = [outy] * number_of_batches_to_generate

inp = torch.LongTensor(inp).cuda()

with ctx:
  out = model.generate(inp,
                        number_of_tokens_to_generate,
                        temperature=temperature,
                        return_prime=True,
                        eos_token=min_stop_token,
                        verbose=True)

out0 = out.tolist()

torch.cuda.empty_cache()

print('=' * 70)
print('Done!')
print('=' * 70)

#======================================================================
print('Rendering results...')

for i in range(number_of_batches_to_generate):

  print('=' * 70)
  print('Batch #', i)
  print('=' * 70)

  out1 = out0[i]

  print('Sample INTs', out1[:12])
  print('=' * 70)

  if len(out) != 0:

      song = out1
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

          if 0 <= ss < 256:

              time += ss * 16

          if 256 <= ss < 2304:

              dur = ((ss-256) // 8) * 16
              vel = (((ss-256) % 8)+1) * 15

          if 2304 <= ss < 18945:

              patch = (ss-2304) // 129

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

              pitch = (ss-2304) % 129

              song_f.append(['note', time, dur, channel, pitch, vel ])

      patches = [0 if x==-1 else x for x in patches]

      detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                                output_signature = 'Giant Music Transformer',
                                                                output_file_name = '/content/Giant-Music-Transformer-Music-Composition_'+str(i),
                                                                track_name='Project Los Angeles',
                                                                list_of_MIDI_patches=patches
                                                                )
      print('=' * 70)
      print('Displaying resulting composition...')
      print('=' * 70)

      fname = '/content/Giant-Music-Transformer-Music-Composition_'+str(i)

      x = []
      y =[]
      c = []

      colors = ['red', 'yellow', 'green', 'cyan',
                'blue', 'pink', 'orange', 'purple',
                'gray', 'white', 'gold', 'silver',
                'lightgreen', 'indigo', 'maroon', 'turquoise']

      for s in song_f:
        x.append(s[1] / 1000)
        y.append(s[4])
        c.append(colors[s[3]])

      if render_MIDI_to_audio:
        midi_audio = midi_to_colab_audio(fname + '.mid')
        display(Audio(midi_audio, rate=16000, normalize=False))

      plt.figure(figsize=(14,5))
      ax=plt.axes(title=fname)
      ax.set_facecolor('black')

      plt.scatter(x,y, c=c)
      ax.axvline(x=block_marker, c='w')

      plt.xlabel("Time")
      plt.ylabel("Pitch")

      plt.show()

"""# Congrats! You did it! :)"""