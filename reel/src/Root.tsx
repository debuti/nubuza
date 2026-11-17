import {Composition} from 'remotion';
import {AriadnaPrueba, DURATION_S} from './reels/AriadnaPrueba';
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="ariadna-prueba" component={AriadnaPrueba} durationInFrames={Math.ceil(DURATION_S * 30)} fps={30} width={1080} height={1920} />
  </>
);
