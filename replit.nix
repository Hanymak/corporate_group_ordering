{ pkgs }: {
  deps = [
    pkgs.systemdMinimal
    pkgs.sqlite.bin
    pkgs.mailutils
    pkgs.replitPackages.prybar-python310
    pkgs.replitPackages.stderred
  ];
}