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
        self.base_dir = base_dir
        self.ensime_version = "0.9.10-SNAPSHOT"
        self.sbt_version = "0.13.8"

    def launch(self, conf_path):
        conf = self.parse_conf(conf_path)
        scala_version = conf['scala-version']
        classpath = self.load_classpath(scala_version)
        return self.start_process(classpath)

    def classpath_project_dir(self, scala_version):
        return os.path.join(self.base_dir, scala_version)

    def load_classpath(self, scala_version):
        project_dir = self.classpath_project_dir(scala_version)
        classpath_file = os.path.join(project_dir, "classpath")
        if not os.path.exists(classpath_file):
            self.generate_classpath(scala_version, classpath_file)
        return self.__read_file(classpath_file)

    def generate_classpath(self, scala_version, classpath_file):
        project_dir = self.classpath_project_dir(scala_version)
        self.__mkdir_p(project_dir)
        self.__mkdir_p(os.path.join(project_dir, "project"))
        sbt = self.build_sbt(scala_version, classpath_file)
        self.__write_file(os.path.join(project_dir, "build.sbt"), sbt)
        self.__write_file(os.path.join(project_dir, "project", "build.properties"),
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
            raise "classpath project build failed: ret={}. See {} for more information".format(ret, log_file)
        return self.__read_file(classpath_file)

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
        conf = self.__read_file(path).replace("\n", "").replace(
                "(", " ").replace(")", " ").replace('"', "").split(" :")
        pattern = re.compile("([^ ]*) *(.*)$")
        conf = [(m[0], m[1])for m in [pattern.match(x).groups() for x in conf]]
        result = {}
        for item in conf:
            result[item[0]] = item[1]
        return result

    def __mkdir_p(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def __read_file(self, path):
        f = open(path)
        result = f.read()
        f.close()
        return result

    def __write_file(self, path, contents):
        f = open(path, "w")
        result = f.write(contents)
        f.close()
        return result

