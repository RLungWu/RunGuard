from runguard.cli import main


def test_cli_main_output(capsys):
    main()
    
    captured = capsys.readouterr()
    
    assert "Hello from runguard!" in captured.out