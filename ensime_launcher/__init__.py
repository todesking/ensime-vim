import os
import signal
import socket
import subprocess
import re
import threading

class EnsimeProcess:
    def __init__(self, config_path):
        return
    def kill(self):
        return
    def open_ws():
        return

class EnsimeLauncher:
    def __init__(self, base_dir =  "/tmp/classpath_project_ensime"):
        self.parse_conf()
        self.classpath_project_dir = classpath_project_dir
        self.classpath_file = os.path.join(self.classpath_project_dir, "classpath")

    def launch(self, conf_path):
        self.__prepare_classpath()
        return self.__start_process()

    def prepare_classpath(self):
        if os.path.exists(self.classpath_file):
            return
        log = None
        classpath = None
        if not os.path.exists(self.classpath_project_dir): os.mkdir(self.classpath_project_dir)
        build_sbt = """
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
        replace = {"scala_version": self.conf['scala-version'], "version": self.version, "classpath_file": self.classpath_file}
        for k in replace.keys():
            build_sbt = build_sbt.replace("%("+k+")", replace[k])
        project_dir = self.__classpath_project_path("project")
        if not os.path.exists(project_dir): os.mkdir(project_dir)
        self.__write_file(self.__classpath_project_path("build.sbt"), build_sbt)
        self.__write_file(self.__classpath_project_path("project", "build.properties"), "sbt.version=0.13.8")
        null = open("/dev/null", "rw")
        process = subprocess.Popen(["sbt", "-batch", "saveClasspath"], stdin = null, stdout = null, stderr = subprocess.STDOUT, cwd = self.classpath_project_dir)
        ret = process.wait()
        if ret != 0:
            raise "classpath project build failed: ret={}".format(ret)

    def __classpath_project_path(*path):
        return os.path.join(self.classpath_project_dir, *path)

    def __start_process(self):
        return

    def parse_conf(self):
        conf = self.read_file(self.conf_path).replace("\n", "").replace(
                "(", " ").replace(")", " ").replace('"', "").split(" :")
        pattern = re.compile("([^ ]*) *(.*)$")
        conf = [(m[0], m[1])for m in [pattern.match(x).groups() for x in conf]]
        result = {}
        for item in conf:
            result[item[0]] = item[1]
        return result
    def __generate_classpath(self):
        if self.generating_classpath:
            return
        self.generating_classpath = True
        log = None
        classpath = None
        if not os.path.exists(self.classpath_file):
            if not os.path.exists(self.classpath_dir): os.mkdir(self.classpath_dir)
            build_sbt = """
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
            replace = {"scala_version": self.conf['scala-version'], "version": self.version, "classpath_file": self.classpath_file}
            for k in replace.keys():
                build_sbt = build_sbt.replace("%("+k+")", replace[k])
            project_dir = "{}/project".format(self.classpath_dir)
            if not os.path.exists(project_dir): os.mkdir(project_dir)
            self.write_file("{}/build.sbt".format(self.classpath_dir), build_sbt)
            self.write_file("{}/project/build.properties".format(self.classpath_dir),
                    "sbt.version=0.13.8")
            self.log_file = open('{}/saveClasspath.log'.format(
                self.classpath_dir), 'w')
            os.system("(cd {};sbt -batch saveClasspath)".format(self.classpath_dir))
    def read_file(self, path):
        f = open(path)
        result = f.read()
        f.close()
        return result
    def write_file(self, path, contents):
        f = open(path, "w")
        result = f.write(contents)
        f.close()
        return result
    def is_running(self):
        port_path = self.conf_path + "_cache/http"
        if not os.path.exists(port_path):
            return False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect("127.0.0.1", int(self.read_file(port_path))).close()
        except:
            return False
        return True
    def setup(self):
        Future(self.__generate_classpath).and_then(self.__set_classpath).join()
    def __set_classpath():
        if os.path.exists(self.classpath_file):
            self.classpath = "{}:{}/lib/tools.jar".format(
                    self.read_file(self.classpath_file),
                    self.conf['java-home'])
    def run(self):
        if self.classpath != None and self.conf != None and not self.is_running():
            if not os.path.exists(self.conf['cache-dir']):
                os.mkdir(self.conf['cache-dir'])
            self.log_file = open(self.conf_path + '_cache/server.log', 'w')
            args = [a for a in [self.conf['java-home'] + "/bin/java"] +
                    self.conf['java-flags'].split(" ") if a != ""] + [
                            "-cp",  self.classpath,
                            "-Densime.config=" + self.conf_path,
                            "org.ensime.server.Server"]
            self.process = subprocess.Popen(args, stdout=self.log_file,
                    stderr=subprocess.STDOUT)
            self.write_file(self.conf_path + "_cache/server.pid",
                str(self.process.pid))
        return self
    def wait(self):
        self.process.wait()
    def stop(self):
        if self.process != None: os.kill(self.process.pid, signal.SIGTERM)
        if self.log_file != None: self.log_file.close()

