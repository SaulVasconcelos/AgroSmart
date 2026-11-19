import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setChromiumOpenGlRenderer('angle');
// O ambiente em que o vídeo foi renderizado tinha 2 núcleos; ajuste à sua máquina.
Config.setConcurrency(2);
