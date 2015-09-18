import os
import signal
import subprocess
import re
import socket

class Util:
    @staticmethod
    def read_file(path):
        f = open(path)
        result = f.read()
        f.close()
        return result

    @staticmethod
    def write_file(path, contents):
        f = open(path, "w")
        result = f.write(contents)
        f.close()
        return result

    @staticmethod
    def mkdir_p(path):
        if not os.path.exists(path):
            os.makedirs(path)

class EnsimeProcess:
    def __init__(self, cache_dir, process, log_path, cleanup):
        self.log_path = log_path
        self.cache_dir = cache_dir
        self.process = process
        self.__stopped_manually = False
        self.__cleanup = cleanup

    def stop(self):
        os.kill(self.process.pid, signal.SIGTERM)
        self.__cleanup()
        self.__stopped_manually = True

    def aborted(self):
        return not (self.__stopped_manually | self.process.poll() == None)

    def is_ready(self):
        if self.process.poll() != None:
            return False
        try:
            port = self.http_port()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect("127.0.0.1", port).close()
            return True
        except:
            return False

    def http_port(self):
        return int(Util.read_file(os.path.join(self.cache_dir, "http")))

class EnsimeLauncher:
    def __init__(self, base_dir =  "/tmp/classpath_project_ensime"):
        self.base_dir = base_dir
        self.ensime_version = "0.9.10-SNAPSHOT"
        self.sbt_version = "0.13.8"

    def launch(self, conf_path):
        conf = self.parse_conf(conf_path)
        classpath = self.load_classpath(conf['scala-version'], conf['java-home'])
        return self.start_process(
                conf_path = conf_path,
                classpath = classpath,
                cache_dir = conf['cache-dir'],
                java_home = conf['java-home'],
                java_flags = conf['java-flags'])

    def classpath_project_dir(self, scala_version):
        return os.path.join(self.base_dir, scala_version)

    def load_classpath(self, scala_version, java_home):
        project_dir = self.classpath_project_dir(scala_version)
        classpath_file = os.path.join(project_dir, "classpath")
        if not os.path.exists(classpath_file):
            self.generate_classpath(scala_version, classpath_file)
        return "{}:{}/tools.jar".format(Util.read_file(classpath_file), java_home)

    def start_process(self, conf_path, classpath, cache_dir, java_home, java_flags):
        Util.mkdir_p(cache_dir)
        log_path = os.path.join(cache_dir, "server.log")
        log = open(log_path, "w")
        null = open("/dev/null", "r")
        args = (
            [os.path.join(java_home, "bin", "java")] +
            [a for a in java_flags.split(" ") if a != ""] +
            ["-Densime.config={}".format(conf_path), "org.ensime.server.Server"])
        process = subprocess.Popen(
                args,
                stdin = null,
                stdout = log,
                stderr = subprocess.STDOUT)
        pid_path = os.path.join(cache_dir, "server.pid")
        Util.write_file(pid_path, str(process.pid))
        def on_stop():
            log.close()
            os.remove(pid_path)
        return EnsimeProcess(cache_dir, process, log_path, on_stop)

    def generate_classpath(self, scala_version, classpath_file):
        project_dir = self.classpath_project_dir(scala_version)
        Util.mkdir_p(project_dir)
        Util.mkdir_p(os.path.join(project_dir, "project"))
        Util.write_file(os.path.join(project_dir, "build.sbt"), self.build_sbt(scala_version, classpath_file))
        Util.write_file(os.path.join(project_dir, "project", "build.properties"),
                self.sbt_version)
        log_file = os.path.join(project_dir, "build.log")
        log = open(log_file, 'w')
        null = open("/dev/null", "r")
        process = subprocess.Popen(
                ["sbt", "-batch", "saveClasspath"],
                stdin = null,
                stdout = log,
                stderr = subprocess.STDOUT,
                cwd = project_dir)
        ret = process.wait()
        log.close()
        null.close()
        if ret != 0:
            raise Exception(
                    "classpath project build failed: exit code = {}. See {} for more information".format(ret, log_file))

    def build_sbt(self, scala_version, classpath_file):
        src = """
import sbt._
import IO._
import java.io._
scalaVersion := "%(scala_version)"
ivyScala := ivyScala.value map { _.copy(overrideScalaVersion = true) }
// allows local builds of scala
resolvers += Resolver.mavenLocal
resolvers += Resolver.sonatypeRepo("snapshots")
resolvers += "Typesafe repository" at "http://repo.typesafe.com/typesafe/releases/"
resolvers += "Akka Repo" at "http://repo.akka.io/repository"
libraryDependencies ++= Seq(
  "org.ensime" %% "ensime" % "%(version)",
  "org.scala-lang" % "scala-compiler" % scalaVersion.value force(),
  "org.scala-lang" % "scala-reflect" % scalaVersion.value force(),
  "org.scala-lang" % "scalap" % scalaVersion.value force()
)
val saveClasspathTask = TaskKey[Unit]("saveClasspath", "Save the classpath to a file")
saveClasspathTask := {
  val managed = (managedClasspath in Runtime).value.map(_.data.getAbsolutePath)
  val unmanaged = (unmanagedClasspath in Runtime).value.map(_.data.getAbsolutePath)
  val out = file("%(classpath_file)")
  write(out, (unmanaged ++ managed).mkString(File.pathSeparator))
}"""
        replace = {
            "scala_version": scala_version,
            "version": self.ensime_version,
            "classpath_file": classpath_file,
            }
        for k in replace.keys():
            src = src.replace("%("+k+")", replace[k])
        return src

    def parse_conf(self, path):
        conf = Util.read_file(path).replace("\n", "").replace(
                "(", " ").replace(")", " ").replace('"', "").split(" :")
        pattern = re.compile("([^ ]*) *(.*)$")
        conf = [(m[0], m[1])for m in [pattern.match(x).groups() for x in conf]]
        result = {}
        for item in conf:
            result[item[0]] = item[1]
        return result
