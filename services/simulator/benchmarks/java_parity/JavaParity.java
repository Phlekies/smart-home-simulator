import io.github.phlekies.smarthome.model.AntennaType;
import io.github.phlekies.smarthome.model.Environment;
import io.github.phlekies.smarthome.model.Sensor;
import io.github.phlekies.smarthome.model.Wall;
import io.github.phlekies.smarthome.model.material.Materials;
import io.github.phlekies.smarthome.simulation.CellResult;
import io.github.phlekies.smarthome.simulation.PropagationEngine;
import io.github.phlekies.smarthome.simulation.PropagationMode;
import io.github.phlekies.smarthome.simulation.SimulationSettings;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Evaluation harness for B-121: runs the original Java propagation engine on cases described
 * line by line on stdin and prints the received power of each probe. Read-only use of the Java
 * sources; compiled into a temporary directory by java_parity.py.
 *
 * <pre>
 * case    id
 * env     freqMHz bandwidthHz noiseFigureDb alphaDbPerM systemGainDb
 * mode    direct|rays|waves exponent receiverGainDb receiverPolarizationDeg
 * wall    x1 y1 x2 y2 materialName thicknessCm
 * sensor  id x y txPowerDbm txGainDb OMNIDIRECTIONAL|DIRECTIONAL orientation beamwidth sharpness sideLobe polarization
 * probe   id sensorId rxX rxY
 * </pre>
 */
public final class JavaParity {
    private JavaParity() {
    }

    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String caseId = "";
        Environment env = new Environment();
        SimulationSettings settings = new SimulationSettings();
        Map<String, Sensor> sensors = new HashMap<>();
        String line;
        while ((line = in.readLine()) != null) {
            String[] f = line.trim().split("\\s+");
            switch (f[0]) {
                case "case" -> {
                    caseId = f[1];
                    env = new Environment();
                    settings = new SimulationSettings();
                    sensors = new HashMap<>();
                }
                case "env" -> {
                    env.setFreqMHz(d(f[1]));
                    env.setBandwidthHz(d(f[2]));
                    env.setNoiseFigureDb(d(f[3]));
                    env.setAlphaDbPerMeter(d(f[4]));
                    env.setSystemGainDb(d(f[5]));
                }
                case "mode" -> {
                    settings.setParallelComputation(false);
                    if (f[1].equals("direct")) {
                        settings.setMaxReflectionPaths(0);
                        settings.setDiffractionEnabled(false);
                        settings.setScatteringEnabled(false);
                        settings.setCullingThresholdDbm(-300.0);
                    } else {
                        settings.setPropagationMode(f[1].equals("waves") ? PropagationMode.WAVES : PropagationMode.RAYS);
                    }
                    settings.setLogDistanceExponent(d(f[2]));
                    settings.setReceiverGainDb(d(f[3]));
                    settings.setReceiverPolarizationDeg(d(f[4]));
                }
                case "wall" -> env.addWall(new Wall(d(f[1]), d(f[2]), d(f[3]), d(f[4]),
                        Materials.byName(f[5].replace('_', ' ')).orElseThrow(), d(f[6])));
                case "sensor" -> {
                    Sensor s = new Sensor(f[1], f[1], Integer.parseInt(f[2]), Integer.parseInt(f[3]));
                    s.setTxPowerDbm(d(f[4]));
                    s.setTxGainDb(d(f[5]));
                    s.setAntennaType(AntennaType.valueOf(f[6]));
                    s.setOrientationDeg(d(f[7]));
                    s.setBeamwidthDeg(d(f[8]));
                    s.setPatternSharpness(d(f[9]));
                    s.setSideLobeAttenuationDb(d(f[10]));
                    s.setPolarizationDeg(d(f[11]));
                    sensors.put(f[1], s);
                }
                case "probe" -> {
                    CellResult cell = PropagationEngine.computeCell(env, List.of(sensors.get(f[2])),
                            d(f[3]), d(f[4]), settings);
                    System.out.printf(Locale.ROOT, "%s %s %.9f %d%n", caseId, f[1], cell.signalPowerDbm(),
                            cell.pathCount());
                }
                default -> {
                    if (!f[0].isEmpty()) throw new IllegalArgumentException("Unknown line: " + line);
                }
            }
        }
    }

    private static double d(String value) {
        return Double.parseDouble(value);
    }
}
